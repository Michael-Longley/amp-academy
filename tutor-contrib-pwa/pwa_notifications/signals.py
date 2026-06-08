"""
Standard LMS signal handlers that fan out push notifications.

Each handler guards its import with try/except so that if tutor-contrib-pwa is
not installed in the LMS the signal connections are simply skipped rather than
raising an ImportError at startup.
"""
from __future__ import annotations

import logging

from django.dispatch import receiver

logger = logging.getLogger(__name__)


def _send(user_id: int, notification_type: str, title: str, body: str, url: str = "") -> None:
    try:
        from tutorpwa.notifications import send_notification
        send_notification(user_id=user_id, notification_type=notification_type, title=title, body=body, url=url)
    except Exception as exc:
        logger.warning("PWA: could not send %r notification: %s", notification_type, exc)


# ── grades.grade_posted ───────────────────────────────────────────────────────
try:
    from lms.djangoapps.grades.signals.signals import SCORE_PUBLISHED

    @receiver(SCORE_PUBLISHED)
    def on_score_published(sender, user_id, course_id, usage_id, weighted_earned, weighted_possible, **kwargs):
        _send(
            user_id=user_id,
            notification_type="grades.grade_posted",
            title="Your grade has been posted",
            body=f"Score: {weighted_earned}/{weighted_possible}",
            url=f"/courses/{course_id}/progress/",
        )
except ImportError:
    pass


# ── enrollment.confirmed ──────────────────────────────────────────────────────
try:
    from common.djangoapps.student.models import ENROLL_STATUS_CHANGE, EnrollStatusChange

    @receiver(ENROLL_STATUS_CHANGE)
    def on_enroll_status_change(sender, event=None, user=None, course_id=None, **kwargs):
        if event == EnrollStatusChange.enroll and user is not None:
            _send(
                user_id=user.id,
                notification_type="enrollment.confirmed",
                title="Enrollment confirmed",
                body=f"You are now enrolled in {course_id}.",
                url=f"/courses/{course_id}/about/",
            )
except ImportError:
    pass


# ── certificates.awarded ──────────────────────────────────────────────────────
try:
    from lms.djangoapps.certificates.signals import CERTIFICATE_CREATED

    @receiver(CERTIFICATE_CREATED)
    def on_certificate_created(sender, user, course_key, certificate, **kwargs):
        _send(
            user_id=user.id,
            notification_type="certificates.awarded",
            title="Certificate awarded",
            body=f"Your certificate for {course_key} is ready.",
            url="/profile/",
        )
except ImportError:
    pass


# ── announcements.course_update ───────────────────────────────────────────────
try:
    from lms.djangoapps.courseware.signals import COURSE_ANNOUNCEMENT

    @receiver(COURSE_ANNOUNCEMENT)
    def on_course_announcement(sender, user_ids=None, course_id=None, subject=None, **kwargs):
        if not user_ids:
            return
        for uid in user_ids:
            _send(
                user_id=uid,
                notification_type="announcements.course_update",
                title="Course announcement",
                body=subject or "A new announcement has been posted.",
                url=f"/courses/{course_id}/updates/",
            )
except ImportError:
    pass
