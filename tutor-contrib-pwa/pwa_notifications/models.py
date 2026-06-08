from django.conf import settings
from django.db import models


class PushSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pwa_subscriptions",
    )
    endpoint = models.TextField(unique=True)
    p256dh = models.TextField()
    auth = models.TextField()
    user_agent = models.CharField(max_length=512, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"PushSubscription(user={self.user_id}, active={self.is_active})"


class NotificationType(models.Model):
    id = models.CharField(max_length=128, primary_key=True)
    label = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.label


class NotificationPreference(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pwa_notification_preferences",
    )
    type = models.ForeignKey(
        NotificationType,
        on_delete=models.CASCADE,
        related_name="preferences",
    )
    enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = [("user", "type")]

    def __str__(self):
        return f"NotificationPreference(user={self.user_id}, type={self.type_id}, enabled={self.enabled})"


DELIVERY_STATUS_CHOICES = [
    ("delivered", "Delivered"),
    ("failed", "Failed"),
    ("skipped_disabled", "Skipped — type disabled"),
    ("skipped_opted_out", "Skipped — user opted out"),
]


class NotificationLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pwa_notification_logs",
    )
    type = models.ForeignKey(
        NotificationType,
        on_delete=models.SET_NULL,
        null=True,
        related_name="logs",
    )
    title = models.CharField(max_length=255)
    body = models.CharField(max_length=1024)
    url = models.CharField(max_length=512, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    delivery_status = models.CharField(max_length=32, choices=DELIVERY_STATUS_CHOICES)

    class Meta:
        ordering = ["-sent_at"]
        indexes = [
            models.Index(fields=["user", "sent_at"]),
        ]

    def __str__(self):
        return f"NotificationLog(user={self.user_id}, status={self.delivery_status})"
