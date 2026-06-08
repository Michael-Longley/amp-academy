"""
Management command: seed the NotificationType table with the standard types.

Creates missing records. Never modifies existing records, preserving
operator-set enabled/disabled choices across plugin upgrades.

Other plugins that add custom types should call NotificationType.objects.get_or_create()
directly in their own migration or management command — not via this command.
"""
from django.core.management.base import BaseCommand

from pwa_notifications.models import NotificationType

# Standard types bundled with the plugin. All disabled by default;
# operators enable what makes sense for their deployment in Django admin.
STANDARD_TYPES = [
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
]


class Command(BaseCommand):
    help = "Seed the NotificationType table with standard PWA notification types."

    def handle(self, *args, **options):
        created_count = 0
        for item in STANDARD_TYPES:
            _, created = NotificationType.objects.get_or_create(
                id=item["id"],
                defaults={
                    "label": item["label"],
                    "description": item.get("description", ""),
                    "enabled": item.get("default_enabled", False),
                },
            )
            if created:
                created_count += 1
                self.stdout.write(f"  Created: {item['id']}")

        self.stdout.write(
            self.style.SUCCESS(
                f"sync_pwa_notification_types: {created_count} created, "
                f"{len(STANDARD_TYPES) - created_count} already exist."
            )
        )
