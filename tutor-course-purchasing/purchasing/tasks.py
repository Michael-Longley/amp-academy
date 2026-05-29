"""Celery tasks for the purchasing plugin."""
from __future__ import annotations

from celery import shared_task
from django.utils import timezone

from . import enrollment
from .models import CourseAccess, Subscription


@shared_task(name="purchasing.tasks.expire_subscription_grace_periods")
def expire_subscription_grace_periods():
    """Deactivate course access and unenroll students whose subscription grace period has ended."""
    now = timezone.now()

    expired_accesses = CourseAccess.objects.filter(
        access_type=CourseAccess.ACCESS_SUBSCRIPTION,
        is_active=True,
        expires_at__lt=now,
    ).select_related("user", "subscription")

    for access in expired_accesses:
        sub = access.subscription
        if sub and sub.status in (Subscription.STATUS_ACTIVE,):
            continue

        access.is_active = False
        access.save(update_fields=["is_active"])

        if sub:
            sub.status = Subscription.STATUS_EXPIRED
            sub.save(update_fields=["status"])

        enrollment.unenroll_user(access.user, access.course_id)
