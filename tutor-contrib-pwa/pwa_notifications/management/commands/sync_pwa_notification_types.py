"""
Management command: sync notification types registered via the Tutor hook into the database.

Creates missing NotificationType records. Never modifies existing records,
preserving operator-set enabled/disabled choices across plugin upgrades.
"""
from django.core.management.base import BaseCommand

from pwa_notifications.models import NotificationType


class Command(BaseCommand):
    help = "Sync PWA_NOTIFICATION_TYPES hook registrations to the NotificationType table."

    def handle(self, *args, **options):
        try:
            from tutorpwa.hooks import PWA_NOTIFICATION_TYPES
            registered = PWA_NOTIFICATION_TYPES.apply([])
        except ImportError:
            self.stderr.write("tutorpwa not installed — skipping sync.")
            return

        created_count = 0
        for item in registered:
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
                f"{len(registered) - created_count} already exist."
            )
        )
