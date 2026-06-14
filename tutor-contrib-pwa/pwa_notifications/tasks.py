from __future__ import annotations

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


# ── Push delivery ─────────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def send_push_notification(self, user_id: int, notification_type_id: str, title: str, body: str, url: str = "") -> None:
    from pwa_notifications.models import NotificationLog, NotificationPreference, NotificationType, PushSubscription

    # 1. Check operator-level enable toggle
    try:
        ntype = NotificationType.objects.get(pk=notification_type_id)
    except NotificationType.DoesNotExist:
        logger.warning("PWA: unknown notification type %r — skipped", notification_type_id)
        return

    if not ntype.enabled:
        NotificationLog.objects.create(
            user_id=user_id,
            type=ntype,
            title=title,
            body=body,
            url=url,
            delivery_status="skipped_disabled",
        )
        return

    # 2. Check student preference
    try:
        pref = NotificationPreference.objects.get(user_id=user_id, type=ntype)
        if not pref.enabled:
            NotificationLog.objects.create(
                user_id=user_id,
                type=ntype,
                title=title,
                body=body,
                url=url,
                delivery_status="skipped_opted_out",
            )
            return
    except NotificationPreference.DoesNotExist:
        pass  # No preference record means default-enabled

    # 3. Deliver to all active subscriptions for this user
    subscriptions = PushSubscription.objects.filter(user_id=user_id, is_active=True)
    if not subscriptions.exists():
        return

    from pywebpush import WebPushException, webpush

    vapid_claims = {
        "sub": f"mailto:{getattr(settings, 'PWA_VAPID_CONTACT_EMAIL', '')}",
    }
    vapid_private_key = getattr(settings, "PWA_VAPID_PRIVATE_KEY", "")

    import json

    for sub in subscriptions:
        payload = json.dumps({"title": title, "body": body, "url": url})
        status = "delivered"
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=payload,
                vapid_private_key=vapid_private_key,
                vapid_claims=vapid_claims,
            )
        except WebPushException as exc:
            response = getattr(exc, "response", None)
            http_status = getattr(response, "status_code", None)
            if http_status == 410:
                # Subscription expired — deactivate silently
                sub.is_active = False
                sub.save(update_fields=["is_active"])
            else:
                logger.error("PWA push failed for sub %s: %s", sub.pk, exc)
            status = "failed"
        except Exception as exc:
            logger.error("PWA push unexpected error for sub %s: %s", sub.pk, exc)
            status = "failed"

        NotificationLog.objects.create(
            user_id=user_id,
            type=ntype,
            title=title,
            body=body,
            url=url,
            delivery_status=status,
        )


# ── Deadlines check (hourly Celery beat task) ─────────────────────────────────

@shared_task
def check_assignment_deadlines() -> None:
    """Fan out push notifications for assignments due in the next 24–25 hours."""
    from pwa_notifications.models import NotificationType

    try:
        NotificationType.objects.get(pk="deadlines.assignment_due_24h", enabled=True)
    except NotificationType.DoesNotExist:
        return  # Type disabled or not synced yet

    now = timezone.now()
    window_start = now + timedelta(hours=24)
    window_end = now + timedelta(hours=25)

    # Query Open edX StudentModuleHistory or StudentModule for upcoming due dates.
    # The exact model depends on the Open edX version; this is a best-effort query.
    try:
        from lms.djangoapps.courseware.models import StudentModule
    except ImportError:
        logger.warning("PWA: could not import StudentModule — deadline check skipped")
        return

    due_items = (
        StudentModule.objects.filter(
            due__gte=window_start,
            due__lt=window_end,
        )
        .select_related("student")
        .values("student_id", "module_state_key", "course_id")
        .distinct()
    )

    for item in due_items:
        send_push_notification.delay(
            user_id=item["student_id"],
            notification_type_id="deadlines.assignment_due_24h",
            title="Assignment due soon",
            body="You have an assignment due in 24 hours.",
            url=f"/courses/{item['course_id']}/courseware/",
        )


# ── Subscription cleanup (weekly Celery beat task) ───────────────────────────

@shared_task
def cleanup_inactive_subscriptions() -> None:
    """Remove stale or inactive push subscriptions older than 90 days."""
    from pwa_notifications.models import PushSubscription

    cutoff = timezone.now() - timedelta(days=90)
    deleted, _ = PushSubscription.objects.filter(
        last_seen__lt=cutoff
    ).delete()
    if deleted:
        logger.info("PWA: cleaned up %d stale push subscriptions", deleted)

    # Also purge explicitly deactivated subscriptions older than 7 days
    week_ago = timezone.now() - timedelta(days=7)
    deleted2, _ = PushSubscription.objects.filter(
        is_active=False,
        last_seen__lt=week_ago,
    ).delete()
    if deleted2:
        logger.info("PWA: purged %d deactivated push subscriptions", deleted2)
