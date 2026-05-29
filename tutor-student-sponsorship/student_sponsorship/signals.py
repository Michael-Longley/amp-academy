"""Enrollment side-effects triggered by Sponsorship status transitions."""
from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import InstitutionCourseAccess, Sponsorship

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Sponsorship)
def on_sponsorship_save(sender, instance, created, **kwargs):
    if created and instance.status == Sponsorship.STATUS_ACTIVE and instance.student:
        _enroll_student(instance)
    elif instance.status == Sponsorship.STATUS_EXPIRED and instance.student:
        _unenroll_student(instance)


def _enroll_student(sponsorship):
    """Enroll the student in all courses granted by their institution."""
    if not sponsorship.student:
        return
    course_ids = InstitutionCourseAccess.objects.filter(
        institution=sponsorship.institution
    ).values_list("course_id", flat=True)

    for course_id in course_ids:
        _safe_enroll(sponsorship.student, course_id)


def _unenroll_student(sponsorship):
    """Deactivate enrollments for courses granted by this institution.

    Only deactivates enrollments that aren't also covered by another active
    sponsorship from a different institution.
    """
    if not sponsorship.student:
        return

    other_active_course_ids = set(
        InstitutionCourseAccess.objects.filter(
            institution__sponsorships__student=sponsorship.student,
            institution__sponsorships__status__in=[
                Sponsorship.STATUS_ACTIVE,
                Sponsorship.STATUS_GRACE,
            ],
        )
        .exclude(institution=sponsorship.institution)
        .values_list("course_id", flat=True)
    )

    course_ids = InstitutionCourseAccess.objects.filter(
        institution=sponsorship.institution
    ).values_list("course_id", flat=True)

    for course_id in course_ids:
        if course_id not in other_active_course_ids:
            _safe_unenroll(sponsorship.student, course_id)


def _safe_enroll(user, course_id_str):
    try:
        from opaque_keys.edx.keys import CourseKey
        from openedx.core.djangoapps.enrollments.api import add_enrollment
        course_key = CourseKey.from_string(course_id_str)
        add_enrollment(user.username, str(course_key), mode="audit", is_active=True)
    except Exception:
        logger.exception(
            "Failed to enroll user %s in course %s", getattr(user, "username", user), course_id_str
        )


def _safe_unenroll(user, course_id_str):
    try:
        from opaque_keys.edx.keys import CourseKey
        from openedx.core.djangoapps.enrollments.api import update_enrollment
        course_key = CourseKey.from_string(course_id_str)
        update_enrollment(user.username, str(course_key), is_active=False)
    except Exception:
        logger.exception(
            "Failed to unenroll user %s from course %s", getattr(user, "username", user), course_id_str
        )
