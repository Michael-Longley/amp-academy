from __future__ import annotations

import uuid
import calendar
from datetime import date, timedelta

import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

COURSE_ID_RE = re.compile(r"^course-v1:[^/+]+\+[^/+]+\+[^/+]+$")
from django.utils import timezone


class Institution(models.Model):
    name           = models.CharField(max_length=255)
    slug           = models.SlugField(unique=True)
    contact_name   = models.CharField(max_length=255, blank=True)
    contact_email  = models.EmailField()
    seat_limit     = models.PositiveIntegerField(
        default=0,
        help_text="Maximum sponsored students. 0 = unlimited.",
    )
    is_active      = models.BooleanField(default=True)
    contract_start = models.DateField()
    contract_end   = models.DateField(null=True, blank=True)
    notes          = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def seats_used(self):
        return self.sponsorships.filter(
            status__in=[Sponsorship.STATUS_ACTIVE, Sponsorship.STATUS_GRACE]
        ).count()

    @property
    def seats_available(self):
        if self.seat_limit == 0:
            return None
        return max(0, self.seat_limit - self.seats_used)


class InstitutionManager(models.Model):
    ROLE_ADMIN   = "admin"
    ROLE_TEACHER = "teacher"
    ROLE_CHOICES = [
        (ROLE_ADMIN,   "Admin"),
        (ROLE_TEACHER, "Teacher"),
    ]

    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE, related_name="managers"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="managed_institutions",
    )
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_ADMIN)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("institution", "user")]

    def __str__(self):
        return f"{self.user} @ {self.institution} ({self.role})"

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_teacher(self):
        return self.role == self.ROLE_TEACHER

    @property
    def display_name(self):
        try:
            from common.djangoapps.student.models import UserProfile
            name = UserProfile.objects.get(user=self.user).name
            return name or self.user.username
        except Exception:
            return self.user.get_full_name() or self.user.username


class Sponsorship(models.Model):
    STATUS_ACTIVE    = "active"
    STATUS_PENDING   = "pending"
    STATUS_GRACE     = "grace"
    STATUS_EXPIRED   = "expired"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_ACTIVE,    "Active"),
        (STATUS_PENDING,   "Pending invitation"),
        (STATUS_GRACE,     "Grace period"),
        (STATUS_EXPIRED,   "Expired"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    institution   = models.ForeignKey(
        Institution, on_delete=models.CASCADE, related_name="sponsorships"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sponsorships",
    )
    invited_email = models.EmailField(
        help_text="Canonical email key. Survives user account deletion."
    )
    status        = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE, db_index=True
    )
    sponsor_start = models.DateField(auto_now_add=True)
    grace_end     = models.DateField(
        null=True, blank=True,
        help_text="Last day of access after sponsorship is removed.",
    )
    removed_at = models.DateTimeField(null=True, blank=True)
    removed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="removed_sponsorships",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["institution", "status"]),
            models.Index(fields=["student", "status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "invited_email"],
                condition=models.Q(status__in=["active", "pending", "grace"]),
                name="unique_active_sponsorship",
            )
        ]

    def __str__(self):
        return f"{self.invited_email} @ {self.institution} [{self.status}]"

    @property
    def student_display_name(self):
        if not self.student:
            return None
        try:
            from common.djangoapps.student.models import UserProfile
            name = UserProfile.objects.get(user=self.student).name
            return name or self.student.username
        except Exception:
            return self.student.get_full_name() or self.student.username

    @property
    def is_accessible(self):
        if self.status == self.STATUS_ACTIVE:
            return True
        if self.status == self.STATUS_GRACE and self.grace_end:
            return date.today() <= self.grace_end
        return False

    def begin_removal(self, removed_by_user, grace_days=0):
        last_day = calendar.monthrange(date.today().year, date.today().month)[1]
        end_of_month = date.today().replace(day=last_day)
        self.grace_end = end_of_month + timedelta(days=grace_days)
        self.status = self.STATUS_GRACE
        self.removed_at = timezone.now()
        self.removed_by = removed_by_user
        self.save()
        # Notify the student that their access will end on grace_end.
        from .emails import send_grace_period_email
        send_grace_period_email(self)


class SponsorshipInvitation(models.Model):
    sponsorship  = models.OneToOneField(
        Sponsorship, on_delete=models.CASCADE, related_name="invitation"
    )
    token       = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    sent_at     = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    expires_at  = models.DateTimeField()

    def __str__(self):
        return f"Invite for {self.sponsorship.invited_email}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_accepted(self):
        return self.accepted_at is not None


class InstitutionCourseAccess(models.Model):
    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE, related_name="course_access"
    )
    course_id = models.CharField(max_length=255, db_index=True)
    subsidy_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of course cost covered by this institution (0–100).",
    )
    added_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("institution", "course_id")]
        verbose_name = "Institution Course Access"
        verbose_name_plural = "Institution Course Access"

    def __str__(self):
        return f"{self.institution} → {self.course_id} ({self.subsidy_pct}%)"

    def clean(self):
        if self.course_id and not COURSE_ID_RE.match(self.course_id):
            raise ValidationError(
                {"course_id": "Must be in Open edX format: course-v1:Org+Course+Run"}
            )


class TeacherStudentAssignment(models.Model):
    teacher = models.ForeignKey(
        InstitutionManager,
        on_delete=models.CASCADE,
        related_name="student_assignments",
        limit_choices_to={"role": InstitutionManager.ROLE_TEACHER},
    )
    sponsorship = models.ForeignKey(
        Sponsorship, on_delete=models.CASCADE, related_name="teacher_assignments"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("teacher", "sponsorship")]
        verbose_name = "Teacher–Student Assignment"
        verbose_name_plural = "Teacher–Student Assignments"

    def __str__(self):
        return f"{self.teacher.user} → {self.sponsorship.invited_email}"
