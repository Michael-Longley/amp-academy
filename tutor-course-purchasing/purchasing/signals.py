"""Post-payment enrollment side-effects."""
from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from . import enrollment
from .models import CourseAccess, Order, Subscription

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal: confirmation email
# ---------------------------------------------------------------------------

def _send_order_confirmation(order: Order) -> None:
    """Send an order confirmation email. Logs on failure; never raises."""
    if not order.user.email:
        return

    currency = getattr(settings, "COURSE_PURCHASING_CURRENCY", "USD")
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@amp-academy.com")
    username = order.user.username
    is_free = order.amount_usd == 0

    # Try to get a human-readable course name (gracefully degrades to course_id)
    try:
        from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
        from opaque_keys.edx.keys import CourseKey
        course_name = CourseOverview.get_from_id(CourseKey.from_string(order.course_id)).display_name
    except Exception:
        course_name = order.course_id

    subject = "Your Amp Academy enrollment is confirmed"

    if is_free:
        price_line_text = "This course is free — no charge was made."
        price_line_html = "<p><strong>This course is free — no charge was made.</strong></p>"
    else:
        price_line_text = f"Amount: ${order.amount_usd} {currency}"
        price_line_html = f"<p>Amount: <strong>${order.amount_usd} {currency}</strong></p>"

    body_text = (
        f"Hi {username},\n\n"
        f"Your enrollment in {course_name!r} is confirmed.\n\n"
        f"{price_line_text}\n"
        f"Order reference: {order.id}\n\n"
        f"Go to your dashboard to start learning:\n"
        f"https://amp-academy.com/dashboard\n\n"
        f"— Amp Academy"
    )

    body_html = f"""<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;font-size:15px;color:#333;max-width:600px;margin:auto;padding:24px;">
<p>Hi {username},</p>
<p>Your enrollment in <strong>{course_name}</strong> is confirmed.</p>
{price_line_html}
<p style="color:#888;font-size:13px;">Order reference: {order.id}</p>
<p>
  <a href="https://amp-academy.com/dashboard"
     style="background:#003057;color:#fff;padding:12px 24px;text-decoration:none;
            border-radius:4px;display:inline-block;font-weight:bold;">
    Start Learning
  </a>
</p>
<hr style="border:none;border-top:1px solid #eee;margin-top:32px;">
<p style="font-size:12px;color:#999;">Amp Academy · <a href="https://amp-academy.com">amp-academy.com</a></p>
</body>
</html>"""

    msg = EmailMultiAlternatives(subject, body_text, from_email, [order.user.email])
    msg.attach_alternative(body_html, "text/html")
    try:
        msg.send()
        logger.debug("Order confirmation sent to %s for order %s", order.user.email, order.id)
    except Exception:
        logger.exception("Failed to send order confirmation for order %s", order.id)


# ---------------------------------------------------------------------------
# Public signal functions
# ---------------------------------------------------------------------------

def complete_order(order: Order, processor_order_id: str = "") -> None:
    """Mark an order complete, create CourseAccess, enroll the student, and confirm by email."""
    order.status = Order.STATUS_COMPLETE
    order.completed_at = timezone.now()
    if processor_order_id:
        order.processor_order_id = processor_order_id
    order.save(update_fields=["status", "completed_at", "processor_order_id"])

    CourseAccess.objects.get_or_create(
        user=order.user,
        course_id=order.course_id,
        order=order,
        defaults={
            "access_type": CourseAccess.ACCESS_ONE_TIME,
            "is_active": True,
            "expires_at": None,
        },
    )
    enrollment.enroll_user(order.user, order.course_id)
    _send_order_confirmation(order)


def complete_subscription_order(order: Order, subscription: Subscription) -> None:
    """Create CourseAccess for a new subscription, enroll the student, and confirm by email."""
    order.status = Order.STATUS_COMPLETE
    order.completed_at = timezone.now()
    order.save(update_fields=["status", "completed_at"])

    CourseAccess.objects.get_or_create(
        user=order.user,
        course_id=order.course_id,
        subscription=subscription,
        defaults={
            "access_type": CourseAccess.ACCESS_SUBSCRIPTION,
            "is_active": True,
            "expires_at": None,
        },
    )
    enrollment.enroll_user(order.user, order.course_id)
    _send_order_confirmation(order)


def revoke_order(order: Order) -> None:
    """Mark an order refunded, deactivate CourseAccess, unenroll the student."""
    order.status = Order.STATUS_REFUNDED
    order.refunded_at = timezone.now()
    order.save(update_fields=["status", "refunded_at"])

    CourseAccess.objects.filter(order=order).update(is_active=False)
    enrollment.unenroll_user(order.user, order.course_id)
