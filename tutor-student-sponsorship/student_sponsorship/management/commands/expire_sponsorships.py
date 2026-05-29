"""Management command for expiring grace-period sponsorships.

Use this as a host-level cron alternative to Celery Beat:
  tutor local exec lms python manage.py lms expire_sponsorships

Recommended cron (daily at 00:05 UTC):
  5 0 * * * tutor local exec lms python manage.py lms expire_sponsorships
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from student_sponsorship.models import Sponsorship


class Command(BaseCommand):
    help = "Expire sponsorships whose grace period has ended."

    def handle(self, *args, **options):
        today = timezone.now().date()
        expired_qs = Sponsorship.objects.filter(
            status=Sponsorship.STATUS_GRACE,
            grace_end__lt=today,
        )
        count = 0
        for sponsorship in expired_qs:
            sponsorship.status = Sponsorship.STATUS_EXPIRED
            sponsorship.save()
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Expired {count} sponsorship(s)."))
