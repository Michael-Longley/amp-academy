from __future__ import annotations
import os
from tutor import hooks

HERE = os.path.dirname(os.path.abspath(__file__))

# ── 1. Config defaults ────────────────────────────────────────────────────────
hooks.Filters.CONFIG_DEFAULTS.add_items([
    ("STUDENT_SPONSORSHIP_GRACE_DAYS", 0),
])

# ── 2. Install the Django app into the LMS Docker image ──────────────────────
# The student_sponsorship Django app is bundled in this same package.
# pip-installing the package makes it importable inside the LMS container.
hooks.Filters.ENV_PATCHES.add_item((
    "openedx-dockerfile-post-python-requirements",
    "RUN pip install "
    "'git+https://github.com/michael-longley/amp-academy.git"
    "#subdirectory=tutor-student-sponsorship'",
))

# ── 3. Register app and inject settings into LMS ─────────────────────────────
hooks.Filters.ENV_PATCHES.add_item((
    "openedx-lms-common-settings",
    """
from celery.schedules import crontab as _crontab

STUDENT_SPONSORSHIP_GRACE_DAYS = {{ STUDENT_SPONSORSHIP_GRACE_DAYS }}

CELERYBEAT_SCHEDULE["expire-sponsorships-daily"] = {
    "task": "student_sponsorship.tasks.expire_grace_period_sponsorships",
    "schedule": _crontab(hour=0, minute=5),
}

CELERYBEAT_SCHEDULE["cleanup-expired-invitations-daily"] = {
    "task": "student_sponsorship.tasks.cleanup_expired_invitations",
    "schedule": _crontab(hour=0, minute=15),
}
""",
))

# ── 4. Run migrations on init ────────────────────────────────────────────────
hooks.Filters.CLI_DO_INIT_TASKS.add_item(
    ("lms", "python manage.py lms migrate student_sponsorship"),
)
