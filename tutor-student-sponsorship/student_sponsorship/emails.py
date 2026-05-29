"""Transactional email helpers for the student sponsorship plugin.

Each public function accepts model instances and sends a single email.
All sends are fire-and-forget — exceptions are logged but never re-raised
so that email failures never break the main request/task flow.

To test locally, configure Mailpit as described in DEVELOPMENT.md and watch
http://localhost:8025 after triggering each action.
"""
from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _from_email() -> str:
    return getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@amp-academy.com")


def _send(subject: str, body_text: str, body_html: str, to_email: str) -> None:
    """Build and dispatch a plain-text + HTML email. Logs on failure."""
    msg = EmailMultiAlternatives(
        subject=subject,
        body=body_text,
        from_email=_from_email(),
        to=[to_email],
    )
    msg.attach_alternative(body_html, "text/html")
    try:
        msg.send()
        logger.debug("Email sent to %s — %s", to_email, subject)
    except Exception:
        logger.exception("Failed to send email to %s (subject: %r)", to_email, subject)


def _html_wrap(content: str) -> str:
    """Minimal HTML envelope so HTML emails render correctly in all clients."""
    return f"""<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;font-size:15px;color:#333;max-width:600px;margin:auto;padding:24px;">
{content}
<hr style="border:none;border-top:1px solid #eee;margin-top:32px;">
<p style="font-size:12px;color:#999;">Amp Academy · <a href="https://amp-academy.com">amp-academy.com</a></p>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Public send functions
# ---------------------------------------------------------------------------

def send_invitation_email(sponsorship, invitation, accept_url: str) -> None:
    """Email a prospective student their sponsorship invitation link.

    Called immediately after SponsorshipInvitation is created.
    """
    institution = sponsorship.institution
    email = sponsorship.invited_email
    expiry = invitation.expires_at.strftime("%B %d, %Y")

    subject = f"You've been invited to learn with {institution.name} on Amp Academy"

    body_text = (
        f"Hi,\n\n"
        f"{institution.name} has sponsored you to access courses on Amp Academy.\n\n"
        f"Click the link below to accept your invitation and get started:\n"
        f"{accept_url}\n\n"
        f"This link expires on {expiry}.\n\n"
        f"If you did not expect this email, you can safely ignore it.\n\n"
        f"— Amp Academy"
    )

    body_html = _html_wrap(f"""
<p>Hi,</p>
<p><strong>{institution.name}</strong> has sponsored you to access courses on
<a href="https://amp-academy.com">Amp Academy</a>.</p>
<p style="margin:24px 0;">
  <a href="{accept_url}"
     style="background:#003057;color:#fff;padding:12px 24px;text-decoration:none;
            border-radius:4px;display:inline-block;font-weight:bold;">
    Accept Invitation
  </a>
</p>
<p>Or copy this link into your browser:<br>
   <a href="{accept_url}">{accept_url}</a></p>
<p>This link expires on <strong>{expiry}</strong>.</p>
<p style="color:#888;font-size:13px;">
  If you did not expect this email, you can safely ignore it.
</p>
""")

    _send(subject, body_text, body_html, email)


def send_activation_email(sponsorship) -> None:
    """Confirm to the student that their sponsorship is now active.

    Called after accept_invitation or claim_sponsorship completes successfully.
    """
    if not sponsorship.student or not sponsorship.student.email:
        return
    institution = sponsorship.institution
    email = sponsorship.student.email
    username = sponsorship.student.username

    subject = f"Your sponsorship with {institution.name} is active"

    body_text = (
        f"Hi {username},\n\n"
        f"Your sponsorship through {institution.name} is now active on Amp Academy.\n\n"
        f"Go to your dashboard to access your courses:\n"
        f"https://amp-academy.com/dashboard\n\n"
        f"— Amp Academy"
    )

    body_html = _html_wrap(f"""
<p>Hi {username},</p>
<p>Your sponsorship through <strong>{institution.name}</strong> is now active on Amp Academy.</p>
<p>
  <a href="https://amp-academy.com/dashboard"
     style="background:#003057;color:#fff;padding:12px 24px;text-decoration:none;
            border-radius:4px;display:inline-block;font-weight:bold;">
    Go to My Courses
  </a>
</p>
<p style="color:#888;font-size:13px;">
  Questions? Contact {institution.name} at
  <a href="mailto:{institution.contact_email}">{institution.contact_email}</a>.
</p>
""")

    _send(subject, body_text, body_html, email)


def send_grace_period_email(sponsorship) -> None:
    """Notify a student that their sponsorship has ended and grace period has started.

    Called from Sponsorship.begin_removal().
    """
    if not sponsorship.student or not sponsorship.student.email:
        return
    institution = sponsorship.institution
    email = sponsorship.student.email
    username = sponsorship.student.username
    grace_end = sponsorship.grace_end.strftime("%B %d, %Y") if sponsorship.grace_end else "soon"

    subject = f"Your sponsorship with {institution.name} has ended"

    body_text = (
        f"Hi {username},\n\n"
        f"Your sponsorship through {institution.name} on Amp Academy has ended.\n\n"
        f"You will continue to have access to your courses until {grace_end}.\n"
        f"After that date, you will lose access unless you enroll independently.\n\n"
        f"Questions? Contact your institution at {institution.contact_email}.\n\n"
        f"— Amp Academy"
    )

    body_html = _html_wrap(f"""
<p>Hi {username},</p>
<p>Your sponsorship through <strong>{institution.name}</strong> on Amp Academy has ended.</p>
<p>You will continue to have access to your courses until
   <strong>{grace_end}</strong>.
   After that date you will lose access unless you enroll independently.</p>
<p style="color:#888;font-size:13px;">
  Questions? Contact {institution.name} at
  <a href="mailto:{institution.contact_email}">{institution.contact_email}</a>.
</p>
""")

    _send(subject, body_text, body_html, email)


def send_expired_email(sponsorship) -> None:
    """Notify a student that their sponsored access has fully expired.

    Called from the Celery expiry task.
    """
    if not sponsorship.student or not sponsorship.student.email:
        return
    institution = sponsorship.institution
    email = sponsorship.student.email
    username = sponsorship.student.username

    subject = f"Your access through {institution.name} has expired"

    body_text = (
        f"Hi {username},\n\n"
        f"Your sponsored access through {institution.name} on Amp Academy has expired.\n\n"
        f"Your course progress has been saved. To regain access, contact your institution "
        f"or enroll independently at amp-academy.com.\n\n"
        f"— Amp Academy"
    )

    body_html = _html_wrap(f"""
<p>Hi {username},</p>
<p>Your sponsored access through <strong>{institution.name}</strong> on Amp Academy
   has expired.</p>
<p>Your course progress has been saved. To regain access, contact your institution or
   <a href="https://amp-academy.com/courses">enroll independently</a>.</p>
<p style="color:#888;font-size:13px;">
  Questions? Contact {institution.name} at
  <a href="mailto:{institution.contact_email}">{institution.contact_email}</a>.
</p>
""")

    _send(subject, body_text, body_html, email)
