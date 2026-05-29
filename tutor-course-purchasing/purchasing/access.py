from __future__ import annotations

from datetime import date
from decimal import Decimal

from .models import CourseAccess


def has_access(user, course_id: str) -> bool:
    """Return True if the user currently has active access to the course.

    Checks our CourseAccess table first, then falls back to the student
    sponsorship plugin if it is installed.
    """
    if not user or not user.is_authenticated:
        return False

    if CourseAccess.objects.filter(user=user, course_id=course_id, is_active=True).exists():
        return True

    try:
        from student_sponsorship.models import InstitutionCourseAccess, Sponsorship

        active = Sponsorship.objects.filter(
            student=user,
            status=Sponsorship.STATUS_ACTIVE,
            institution__course_access__course_id=course_id,
        ).exists()
        if active:
            return True

        grace_ok = Sponsorship.objects.filter(
            student=user,
            status=Sponsorship.STATUS_GRACE,
            grace_end__gte=date.today(),
            institution__course_access__course_id=course_id,
        ).exists()
        if grace_ok:
            return True
    except ImportError:
        pass

    return False


def _make_line_item(label: str, amount: Decimal, item_type: str) -> dict:
    """Build a price breakdown line item with a pre-formatted display string."""
    if amount < 0:
        display = f"-${abs(amount):.2f}"
    else:
        display = f"${amount:.2f}"
    return {"label": label, "amount": amount, "display": display, "type": item_type}


def calculate_price(user, course_id: str, base_price: Decimal) -> tuple[list, Decimal]:
    """Return (line_items, final_price) applying any applicable sponsorship discounts.

    line_items is a list of dicts with keys:
      - 'label'   (str)     — human-readable description
      - 'amount'  (Decimal) — raw value; negative for discounts
      - 'display' (str)     — pre-formatted e.g. "$49.00" or "-$4.90"
      - 'type'    (str)     — 'base' | 'sponsorship' | 'free'

    final_price is always >= 0.00.
    """
    if not base_price or base_price <= Decimal("0.00"):
        items = [_make_line_item("Course price", Decimal("0.00"), "free")]
        return items, Decimal("0.00")

    items = [_make_line_item("Course price", base_price, "base")]

    if user and user.is_authenticated:
        try:
            from student_sponsorship.models import InstitutionCourseAccess, Sponsorship

            sponsorship = (
                Sponsorship.objects.filter(
                    student=user,
                    status__in=[Sponsorship.STATUS_ACTIVE, Sponsorship.STATUS_GRACE],
                    institution__course_access__course_id=course_id,
                )
                .select_related("institution")
                .first()
            )

            if sponsorship:
                ica = InstitutionCourseAccess.objects.filter(
                    institution=sponsorship.institution,
                    course_id=course_id,
                ).first()
                if ica and ica.subsidy_pct > 0:
                    discount = (base_price * ica.subsidy_pct / 100).quantize(Decimal("0.01"))
                    pct_display = ica.subsidy_pct.normalize()
                    label = f"{sponsorship.institution.name} ({pct_display}% sponsorship)"
                    items.append(_make_line_item(label, -discount, "sponsorship"))
        except ImportError:
            pass

    final_price = max(sum(i["amount"] for i in items), Decimal("0.00"))
    return items, final_price


def get_processor():
    """Return the configured payment processor instance."""
    from django.conf import settings
    from importlib import import_module

    processor_name = getattr(settings, "COURSE_PURCHASING_PROCESSOR", "stub")

    if processor_name == "stub":
        from .processors.stub import StubProcessor
        return StubProcessor()

    # Future: dynamic import for third-party processors
    raise ValueError(f"Unknown payment processor: {processor_name!r}")
