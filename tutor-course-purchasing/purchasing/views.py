from __future__ import annotations

import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from datetime import timedelta

from django.utils import timezone
from django.views.decorators.http import require_POST

from .access import calculate_price, get_processor, has_access
from .models import CourseAccess, CoursePrice, Order, Subscription
from . import signals as purchasing_signals


# ── Cart helpers (session-based) ──────────────────────────────────────────────

CART_KEY = "purchasing_cart"


def _get_cart(request):
    return request.session.get(CART_KEY, [])


def _save_cart(request, cart):
    request.session[CART_KEY] = cart
    request.session.modified = True


def _get_course_name(course_id: str) -> str:
    """Try to look up the human-readable course name from Open edX."""
    try:
        from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
        from opaque_keys.edx.keys import CourseKey
        key = CourseKey.from_string(course_id)
        overview = CourseOverview.get_from_id(key)
        return overview.display_name
    except Exception:
        return course_id


def _resolve_revenue_split(course_id: str):
    """Return (writer_user_id, writer_share_pct) for a course, falling back to global default."""
    from .models import RevenueSplit
    split = (
        RevenueSplit.objects.filter(course_id=course_id).first()
        or RevenueSplit.objects.filter(course_id__isnull=True).first()
    )
    if split:
        return split.writer_user_id, split.writer_share_pct
    from django.conf import settings
    default_pct = Decimal(str(getattr(settings, "COURSE_PURCHASING_DEFAULT_WRITER_SHARE_PCT", 70)))
    return None, default_pct


def _build_checkout_items(raw: list, user) -> tuple[list, Decimal]:
    """Return (checkout_items, grand_total) with per-item price breakdowns."""
    checkout_items = []
    grand_total = Decimal("0.00")
    for entry in raw:
        base_price = Decimal(str(entry["price_usd"]))
        course_id = entry["course_id"]
        order_type = entry["order_type"]
        line_items, final_price = calculate_price(user, course_id, base_price)
        grand_total += final_price
        checkout_items.append({
            "course_id": course_id,
            "course_name": entry.get("course_name", course_id),
            "order_type": order_type,
            "order_type_label": "One-time" if order_type == "one_time" else "Monthly subscription",
            "base_price": base_price,
            "line_items": line_items,
            "final_price": final_price,
            "final_price_display": f"${final_price:.2f}",
        })
    return checkout_items, grand_total


# ── Views ─────────────────────────────────────────────────────────────────────

def catalog(request):
    prices = CoursePrice.objects.filter(is_active=True)
    items = []
    for price in prices:
        items.append({
            "price": price,
            "course_name": _get_course_name(price.course_id),
            "user_has_access": has_access(request.user, price.course_id),
        })
    return render(request, "purchasing/catalog.html", {"items": items})


@login_required
def cart(request):
    raw = _get_cart(request)
    cart_items = []
    subtotal = Decimal("0.00")
    for entry in raw:
        try:
            price_obj = CoursePrice.objects.get(course_id=entry["course_id"], is_active=True)
        except CoursePrice.DoesNotExist:
            continue
        amount = Decimal(str(entry["price_usd"]))
        subtotal += amount
        cart_items.append({
            "course_id": entry["course_id"],
            "course_name": entry.get("course_name", entry["course_id"]),
            "order_type": entry["order_type"],
            "order_type_label": "One-time" if entry["order_type"] == "one_time" else "Monthly subscription",
            "price_usd": amount,
            "price_obj": price_obj,
        })
    return render(request, "purchasing/cart.html", {
        "cart_items": cart_items,
        "subtotal": subtotal,
    })


@login_required
@require_POST
def cart_add(request):
    course_id = request.POST.get("course_id", "").strip()
    order_type = request.POST.get("order_type", "one_time")

    try:
        price_obj = CoursePrice.objects.get(course_id=course_id, is_active=True)
    except CoursePrice.DoesNotExist:
        messages.error(request, "Course not found.")
        return redirect("purchasing:catalog")

    if price_obj.is_free:
        # Free courses: always one-time access, $0 price
        price_usd = "0.00"
        order_type = "one_time"
    elif order_type == "one_time" and price_obj.offers_one_time:
        price_usd = str(price_obj.one_time_price_usd)
    elif order_type == "subscription" and price_obj.offers_subscription:
        price_usd = str(price_obj.subscription_price_usd)
    else:
        messages.error(request, "Invalid purchase option.")
        return redirect("purchasing:catalog")

    cart = _get_cart(request)
    # Replace existing entry for same course if present
    cart = [c for c in cart if c["course_id"] != course_id]
    cart.append({
        "course_id": course_id,
        "order_type": order_type,
        "price_usd": price_usd,
        "course_name": _get_course_name(course_id),
    })
    _save_cart(request, cart)
    messages.success(request, f"Added to cart.")
    return redirect("purchasing:cart")


@login_required
@require_POST
def cart_remove(request):
    course_id = request.POST.get("course_id", "").strip()
    cart = [c for c in _get_cart(request) if c["course_id"] != course_id]
    _save_cart(request, cart)
    return redirect("purchasing:cart")


@login_required
def checkout(request):
    raw = _get_cart(request)
    if not raw:
        return redirect("purchasing:cart")

    if request.method == "POST":
        # Always re-calculate price server-side — never trust the client.
        checkout_items, grand_total = _build_checkout_items(raw, request.user)
        processor = get_processor()
        completed_orders = []

        for item in checkout_items:
            course_id = item["course_id"]
            order_type = item["order_type"]
            final_price = item["final_price"]
            writer_user_id, writer_share_pct = _resolve_revenue_split(course_id)
            writer_share = (final_price * writer_share_pct / 100).quantize(Decimal("0.01"))
            platform_share = final_price - writer_share

            if order_type == "one_time":
                order = Order.objects.create(
                    user=request.user,
                    course_id=course_id,
                    order_type=Order.TYPE_ONE_TIME,
                    amount_usd=final_price,
                    writer_share_usd=writer_share,
                    platform_share_usd=platform_share,
                    writer_user_id_snapshot=writer_user_id,
                    processor_name="free" if final_price == Decimal("0.00") else "stub",
                    status=Order.STATUS_PENDING,
                )
                if final_price == Decimal("0.00"):
                    # No payment needed — complete immediately.
                    purchasing_signals.complete_order(order)
                else:
                    session = processor.create_one_time_checkout(
                        order,
                        success_url=request.build_absolute_uri(reverse("purchasing:confirmation")),
                        cancel_url=request.build_absolute_uri(reverse("purchasing:cart")),
                    )
                    order.processor_session_id = session.session_id
                    order.save(update_fields=["processor_session_id"])
                    purchasing_signals.complete_order(order)
                completed_orders.append(order)

            elif order_type == "subscription":
                order = Order.objects.create(
                    user=request.user,
                    course_id=course_id,
                    order_type=Order.TYPE_SUBSCRIPTION_START,
                    amount_usd=final_price,
                    writer_share_usd=writer_share,
                    platform_share_usd=platform_share,
                    writer_user_id_snapshot=writer_user_id,
                    processor_name="free" if final_price == Decimal("0.00") else "stub",
                    status=Order.STATUS_PENDING,
                )
                subscription = Subscription.objects.create(
                    user=request.user,
                    course_id=course_id,
                    processor_name="free" if final_price == Decimal("0.00") else "stub",
                    processor_subscription_id=f"stub-sub-{order.id.hex[:8]}",
                    status=Subscription.STATUS_ACTIVE,
                    current_period_end=timezone.now() + timedelta(days=30),
                )
                if final_price == Decimal("0.00"):
                    purchasing_signals.complete_subscription_order(order, subscription)
                else:
                    session = processor.create_subscription_checkout(
                        request.user,
                        None,
                        success_url=request.build_absolute_uri(reverse("purchasing:confirmation")),
                        cancel_url=request.build_absolute_uri(reverse("purchasing:cart")),
                    )
                    order.processor_session_id = session.session_id
                    order.save(update_fields=["processor_session_id"])
                    purchasing_signals.complete_subscription_order(order, subscription)
                completed_orders.append(order)

        _save_cart(request, [])
        request.session["purchasing_last_order_ids"] = [str(o.id) for o in completed_orders]
        return redirect("purchasing:confirmation")

    # GET — build breakdown for display only.
    checkout_items, grand_total = _build_checkout_items(raw, request.user)
    from django.conf import settings
    processor_name = getattr(settings, "COURSE_PURCHASING_PROCESSOR", "stub")
    is_free = grand_total == Decimal("0.00")
    return render(request, "purchasing/checkout.html", {
        "checkout_items": checkout_items,
        "grand_total": grand_total,
        "grand_total_display": f"${grand_total:.2f}",
        "is_free": is_free,
        "is_stub": processor_name == "stub" and not is_free,
    })


@login_required
def confirmation(request):
    order_ids = request.session.pop("purchasing_last_order_ids", [])
    orders = Order.objects.filter(id__in=order_ids, user=request.user)
    return render(request, "purchasing/confirmation.html", {"orders": orders})


@login_required
def orders(request):
    user_orders = Order.objects.filter(user=request.user).order_by("-created_at")
    user_subscriptions = Subscription.objects.filter(
        user=request.user
    ).exclude(status=Subscription.STATUS_EXPIRED).order_by("-created_at")
    return render(request, "purchasing/orders.html", {
        "orders": user_orders,
        "subscriptions": user_subscriptions,
    })


@login_required
@require_POST
def subscription_cancel(request, subscription_id):
    sub = get_object_or_404(Subscription, id=subscription_id, user=request.user)
    if sub.status not in (Subscription.STATUS_ACTIVE, Subscription.STATUS_PAST_DUE, Subscription.STATUS_GRACE_PERIOD):
        messages.error(request, "This subscription cannot be cancelled.")
        return redirect("purchasing:orders")

    processor = get_processor()
    processor.cancel_subscription(sub)
    sub.status = Subscription.STATUS_CANCELLED
    sub.cancelled_at = timezone.now()
    sub.save(update_fields=["status", "cancelled_at"])

    CourseAccess.objects.filter(subscription=sub).update(is_active=False)
    from . import enrollment
    enrollment.unenroll_user(request.user, sub.course_id)

    messages.success(request, "Subscription cancelled.")
    return redirect("purchasing:orders")
