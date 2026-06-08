"""
Public API for sending push notifications from other Tutor plugins.

Usage:

    try:
        from tutorpwa.notifications import send_notification
        _PWA_AVAILABLE = True
    except ImportError:
        _PWA_AVAILABLE = False

    if _PWA_AVAILABLE:
        send_notification(
            user_id=student.id,
            notification_type="sponsorship.payment_due",
            title="Payment required soon",
            body="Your sponsorship ends in 7 days.",
            url="/account/payment",
        )
"""
from __future__ import annotations


def send_notification(
    user_id: int,
    notification_type: str,
    title: str,
    body: str,
    url: str = "",
) -> None:
    """Enqueue a push notification for delivery. Non-blocking."""
    if not user_id or not notification_type or not title:
        raise ValueError("user_id, notification_type, and title are required")

    from pwa_notifications.tasks import send_push_notification

    send_push_notification.delay(
        user_id=user_id,
        notification_type_id=notification_type,
        title=title,
        body=body,
        url=url,
    )
