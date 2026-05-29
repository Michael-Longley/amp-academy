"""Thin wrapper around Open edX's internal enrollment API.

All imports are deferred so this module can be imported outside the LMS
(e.g. during local development or testing) without crashing.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def enroll_user(user, course_id_str: str) -> None:
    try:
        from opaque_keys.edx.keys import CourseKey
        from openedx.core.djangoapps.enrollments.api import add_enrollment
        course_key = CourseKey.from_string(course_id_str)
        add_enrollment(user.username, str(course_key), mode="audit", is_active=True)
    except Exception:
        logger.exception(
            "Failed to enroll user %s in course %s", getattr(user, "username", user), course_id_str
        )


def unenroll_user(user, course_id_str: str) -> None:
    try:
        from opaque_keys.edx.keys import CourseKey
        from openedx.core.djangoapps.enrollments.api import update_enrollment
        course_key = CourseKey.from_string(course_id_str)
        update_enrollment(user.username, str(course_key), is_active=False)
    except Exception:
        logger.exception(
            "Failed to unenroll user %s from course %s", getattr(user, "username", user), course_id_str
        )
