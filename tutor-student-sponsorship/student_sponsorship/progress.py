"""Helpers for reading student progress from Open edX internals.

All Open edX imports are guarded so this module is importable on the host
(for `tutor plugins enable`) without Open edX being installed.
"""
from __future__ import annotations

from django.core.cache import cache

try:
    from common.djangoapps.student.models import CourseEnrollment
    from lms.djangoapps.grades.api import CourseGradeFactory
    from lms.djangoapps.courseware.models import StudentModule
    _OPENEDX_AVAILABLE = True
except ImportError:
    _OPENEDX_AVAILABLE = False


def get_student_progress_summary(user, cache_timeout=900):
    """Return a dict with courses list and last_login for the given user.

    Each course entry: {course_id, display_name, percent, passed, last_activity}.
    Cached per-user for cache_timeout seconds (default 15 min).
    """
    cache_key = f"sponsorship_progress_{user.pk}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    result = {"courses": [], "last_login": user.last_login}

    if not _OPENEDX_AVAILABLE:
        return result

    enrollments = (
        CourseEnrollment.objects.filter(user=user, is_active=True)
        .select_related("course")
    )
    factory = CourseGradeFactory()
    courses = []
    for enrollment in enrollments:
        try:
            grade = factory.read(user, course_key=enrollment.course_id)
            percent = round((grade.percent or 0.0) * 100, 1)
            passed = grade.passed
        except Exception:
            percent = 0.0
            passed = False

        last_activity = (
            StudentModule.objects.filter(
                student=user, course_id=enrollment.course_id
            )
            .order_by("-modified")
            .values_list("modified", flat=True)
            .first()
        )

        courses.append({
            "course_id": str(enrollment.course_id),
            "display_name": getattr(enrollment.course, "display_name", str(enrollment.course_id)),
            "percent": percent,
            "passed": passed,
            "last_activity": last_activity,
        })

    result["courses"] = courses
    cache.set(cache_key, result, timeout=cache_timeout)
    return result


def invalidate_progress_cache(user):
    cache.delete(f"sponsorship_progress_{user.pk}")
