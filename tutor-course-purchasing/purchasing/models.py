from __future__ import annotations

import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class CoursePrice(models.Model):
    PRICING_FREE = "free"
    PRICING_ONE_TIME = "one_time"
    PRICING_SUBSCRIPTION = "subscription"
    PRICING_BOTH = "both"
    PRICING_CHOICES = [
        (PRICING_FREE, "Free"),
        (PRICING_ONE_TIME, "One-time purchase"),
        (PRICING_SUBSCRIPTION, "Subscription only"),
        (PRICING_BOTH, "One-time & Subscription"),
    ]

    course_id = models.CharField(max_length=255, unique=True, db_index=True)
    one_time_price_usd = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Leave blank if one-time purchase is not offered.",
    )
    subscription_price_usd = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Monthly subscription price. Leave blank if subscription is not offered.",
    )
    pricing_options = models.CharField(
        max_length=20, choices=PRICING_CHOICES, default=PRICING_ONE_TIME,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["course_id"]
        verbose_name = "Course Price"
        verbose_name_plural = "Course Prices"

    def __str__(self):
        return f"{self.course_id} ({self.get_pricing_options_display()})"

    @property
    def is_free(self):
        return self.pricing_options == self.PRICING_FREE

    @property
    def offers_one_time(self):
        return self.pricing_options in (self.PRICING_ONE_TIME, self.PRICING_BOTH)

    @property
    def offers_subscription(self):
        return self.pricing_options in (self.PRICING_SUBSCRIPTION, self.PRICING_BOTH)


class RevenueSplit(models.Model):
    course_id = models.CharField(
        max_length=255, null=True, blank=True, db_index=True,
        help_text="Leave blank for the global platform default.",
    )
    writer_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="revenue_splits",
    )
    writer_share_pct = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Writer's share as a percentage (e.g. 70.00).",
    )
    set_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="revenue_splits_configured",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Revenue Split"
        verbose_name_plural = "Revenue Splits"

    def __str__(self):
        scope = self.course_id or "global default"
        return f"{self.writer_user} — {self.writer_share_pct}% ({scope})"

    @property
    def platform_share_pct(self):
        return 100 - self.writer_share_pct


class Order(models.Model):
    TYPE_ONE_TIME = "one_time"
    TYPE_SUBSCRIPTION_START = "subscription_start"
    TYPE_CHOICES = [
        (TYPE_ONE_TIME, "One-time purchase"),
        (TYPE_SUBSCRIPTION_START, "Subscription start"),
    ]

    STATUS_PENDING = "pending"
    STATUS_COMPLETE = "complete"
    STATUS_FAILED = "failed"
    STATUS_REFUNDED = "refunded"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_COMPLETE, "Complete"),
        (STATUS_FAILED, "Failed"),
        (STATUS_REFUNDED, "Refunded"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="purchasing_orders",
    )
    course_id = models.CharField(max_length=255, db_index=True)
    order_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)
    writer_share_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_share_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    writer_user_id_snapshot = models.IntegerField(
        null=True, blank=True,
        help_text="Snapshot of writer user ID at purchase time for future payout reference.",
    )
    processor_name = models.CharField(max_length=50, default="stub")
    processor_session_id = models.CharField(max_length=255, blank=True)
    processor_order_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Order"

    def __str__(self):
        return f"Order {self.id} — {self.user} — {self.course_id} ({self.status})"


class Subscription(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_PAST_DUE = "past_due"
    STATUS_GRACE_PERIOD = "grace_period"
    STATUS_CANCELLED = "cancelled"
    STATUS_EXPIRED = "expired"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_PAST_DUE, "Past due"),
        (STATUS_GRACE_PERIOD, "Grace period"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_EXPIRED, "Expired"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="purchasing_subscriptions",
    )
    course_id = models.CharField(max_length=255, db_index=True)
    processor_name = models.CharField(max_length=50, default="stub")
    processor_subscription_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE, db_index=True,
    )
    current_period_end = models.DateTimeField()
    grace_period_end = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Subscription"

    def __str__(self):
        return f"Sub {self.id} — {self.user} — {self.course_id} ({self.status})"

    @property
    def is_accessible(self):
        from django.utils import timezone
        if self.status == self.STATUS_ACTIVE:
            return True
        if self.status == self.STATUS_GRACE_PERIOD and self.grace_period_end:
            return timezone.now() <= self.grace_period_end
        return False


class CourseAccess(models.Model):
    ACCESS_ONE_TIME = "one_time"
    ACCESS_SUBSCRIPTION = "subscription"
    ACCESS_FREE = "free"
    ACCESS_SPONSORSHIP = "sponsorship"
    ACCESS_CHOICES = [
        (ACCESS_ONE_TIME, "One-time purchase (lifetime)"),
        (ACCESS_SUBSCRIPTION, "Subscription"),
        (ACCESS_FREE, "Free course"),
        (ACCESS_SPONSORSHIP, "Institutional sponsorship"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="course_accesses",
    )
    course_id = models.CharField(max_length=255, db_index=True)
    access_type = models.CharField(max_length=20, choices=ACCESS_CHOICES)
    order = models.ForeignKey(
        Order, on_delete=models.SET_NULL, null=True, blank=True, related_name="accesses",
    )
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name="accesses",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    expires_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Null = lifetime access (one_time, free). Set for subscriptions in grace period.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "course_id", "is_active"]),
        ]
        verbose_name = "Course Access"
        verbose_name_plural = "Course Accesses"

    def __str__(self):
        return f"{self.user} → {self.course_id} [{self.access_type}, active={self.is_active}]"
