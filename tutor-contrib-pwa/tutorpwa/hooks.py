"""
Exported hooks for tutor-contrib-pwa.

Other Tutor plugins register push notification types using PWA_NOTIFICATION_TYPES:

    from tutorpwa.hooks import PWA_NOTIFICATION_TYPES

    PWA_NOTIFICATION_TYPES.add_item({
        "id": "sponsorship.payment_due",
        "label": "Sponsorship payment upcoming",
        "description": "Sent when a sponsored student's funding period is ending.",
        "default_enabled": True,
    })
"""
from tutor.core.hooks import Filter

# Filter: list of notification type dicts — {id, label, description, default_enabled}
PWA_NOTIFICATION_TYPES: Filter = Filter()

# ── Register the 5 standard LMS notification types ───────────────────────────
# All are disabled by default; operators enable them in Django admin.
PWA_NOTIFICATION_TYPES.add_items([
    {
        "id": "grades.grade_posted",
        "label": "Grade posted",
        "description": "Sent when a grade is published for a student.",
        "default_enabled": False,
    },
    {
        "id": "enrollment.confirmed",
        "label": "Enrollment confirmed",
        "description": "Sent when a student successfully enrolls in a course.",
        "default_enabled": False,
    },
    {
        "id": "deadlines.assignment_due_24h",
        "label": "Assignment due in 24 hours",
        "description": "Sent hourly for assignments due in the next 24–25 hour window.",
        "default_enabled": False,
    },
    {
        "id": "certificates.awarded",
        "label": "Certificate awarded",
        "description": "Sent when a certificate is generated for a student.",
        "default_enabled": False,
    },
    {
        "id": "announcements.course_update",
        "label": "Course announcement",
        "description": "Sent when an instructor posts a course-wide announcement.",
        "default_enabled": False,
    },
])
