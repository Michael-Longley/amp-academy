from __future__ import annotations
from tutor import hooks

# ── 1. Config defaults ────────────────────────────────────────────────────────
hooks.Filters.CONFIG_DEFAULTS.add_items([
    ("COURSE_PURCHASING_PROCESSOR", "stub"),
    ("COURSE_PURCHASING_DEFAULT_WRITER_SHARE_PCT", 70),
    ("COURSE_PURCHASING_GRACE_PERIOD_DAYS", 5),
    ("COURSE_PURCHASING_CURRENCY", "USD"),
    ("COURSE_PURCHASING_PROCESSOR_PUBLIC_KEY", ""),
    ("COURSE_PURCHASING_PROCESSOR_SECRET_KEY", ""),
    ("COURSE_PURCHASING_WEBHOOK_SECRET", ""),
    ("COURSE_PURCHASING_FROM_EMAIL", "noreply@amp-academy.com"),
    # Set to true with: tutor config save --set COURSE_PURCHASING_DEV_MAILPIT=true
    # Adds a Mailpit SMTP capture container to the local docker-compose stack.
    # Never enable in production — emails would be silently discarded.
    ("COURSE_PURCHASING_DEV_MAILPIT", False),
])

# ── 2. Install the Django app into the LMS Docker image ──────────────────────
hooks.Filters.ENV_PATCHES.add_item((
    "openedx-dockerfile-post-python-requirements",
    "RUN pip install "
    "'git+https://github.com/michael-longley/amp-academy.git"
    "#subdirectory=tutor-course-purchasing'",
))

# ── 3. Inject Celery beat schedule and purchasing settings into LMS ───────────
hooks.Filters.ENV_PATCHES.add_item((
    "openedx-lms-common-settings",
    """
from celery.schedules import crontab as _crontab

COURSE_PURCHASING_PROCESSOR = "{{ COURSE_PURCHASING_PROCESSOR }}"
COURSE_PURCHASING_DEFAULT_WRITER_SHARE_PCT = {{ COURSE_PURCHASING_DEFAULT_WRITER_SHARE_PCT }}
COURSE_PURCHASING_GRACE_PERIOD_DAYS = {{ COURSE_PURCHASING_GRACE_PERIOD_DAYS }}
COURSE_PURCHASING_CURRENCY = "{{ COURSE_PURCHASING_CURRENCY }}"
COURSE_PURCHASING_PROCESSOR_PUBLIC_KEY = "{{ COURSE_PURCHASING_PROCESSOR_PUBLIC_KEY }}"
COURSE_PURCHASING_PROCESSOR_SECRET_KEY = "{{ COURSE_PURCHASING_PROCESSOR_SECRET_KEY }}"
COURSE_PURCHASING_WEBHOOK_SECRET = "{{ COURSE_PURCHASING_WEBHOOK_SECRET }}"

DEFAULT_FROM_EMAIL = "{{ COURSE_PURCHASING_FROM_EMAIL }}"

CELERYBEAT_SCHEDULE["purchasing-expire-grace-periods-daily"] = {
    "task": "purchasing.tasks.expire_subscription_grace_periods",
    "schedule": _crontab(hour=0, minute=10),
}
""",
))

# ── 4. Mailpit SMTP capture service (dev only) ────────────────────────────────
# Injected into Tutor's local docker-compose when COURSE_PURCHASING_DEV_MAILPIT=true.
# The service joins tutor_local_default automatically so the LMS can reach it at
# hostname "mailpit" on port 1025. View captured mail at http://localhost:8025.
# Enable once with: tutor config save --set COURSE_PURCHASING_DEV_MAILPIT=true
# Then set SMTP: tutor config save --set SMTP_HOST=mailpit --set SMTP_PORT=1025
#                                  --set SMTP_USE_TLS=false
hooks.Filters.ENV_PATCHES.add_item((
    "local-docker-compose-services",
    """{% if COURSE_PURCHASING_DEV_MAILPIT %}
  mailpit:
    image: axllent/mailpit:latest
    restart: unless-stopped
    ports:
      - "127.0.0.1:8025:8025"
      - "127.0.0.1:1025:1025"
{% endif %}""",
))

# ── 5. Run migrations on init ─────────────────────────────────────────────────
hooks.Filters.CLI_DO_INIT_TASKS.add_item(
    ("lms", "python manage.py lms migrate purchasing"),
)
