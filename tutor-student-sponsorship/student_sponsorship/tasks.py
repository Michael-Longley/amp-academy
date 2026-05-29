from celery import shared_task
from django.utils import timezone


@shared_task(name="student_sponsorship.tasks.expire_grace_period_sponsorships")
def expire_grace_period_sponsorships():
    """Expire sponsorships whose grace period has ended and notify each student. Run daily."""
    from .models import Sponsorship
    from .emails import send_expired_email

    today = timezone.now().date()
    expired_qs = Sponsorship.objects.filter(
        status=Sponsorship.STATUS_GRACE,
        grace_end__lt=today,
    ).select_related("student", "institution")

    count = 0
    for sponsorship in expired_qs:
        sponsorship.status = Sponsorship.STATUS_EXPIRED
        sponsorship.save(update_fields=["status", "updated_at"])
        send_expired_email(sponsorship)
        count += 1

    return f"Expired {count} sponsorship(s)."


@shared_task(name="student_sponsorship.tasks.cleanup_expired_invitations")
def cleanup_expired_invitations():
    """Delete SponsorshipInvitations that expired more than 14 days ago. Run daily."""
    from .models import SponsorshipInvitation
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(days=14)
    deleted, _ = SponsorshipInvitation.objects.filter(
        expires_at__lt=cutoff,
        accepted_at__isnull=True,
    ).delete()

    return f"Deleted {deleted} expired invitation(s)."
