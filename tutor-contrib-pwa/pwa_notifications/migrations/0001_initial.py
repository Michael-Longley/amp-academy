from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationType",
            fields=[
                ("id", models.CharField(max_length=128, primary_key=True, serialize=False)),
                ("label", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("enabled", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="PushSubscription",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ("endpoint", models.TextField(unique=True)),
                ("p256dh", models.TextField()),
                ("auth", models.TextField()),
                ("user_agent", models.CharField(blank=True, max_length=512)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_seen", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pwa_subscriptions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="NotificationPreference",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ("enabled", models.BooleanField(default=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pwa_notification_preferences",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="preferences",
                        to="pwa_notifications.notificationtype",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="NotificationLog",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
                ("body", models.CharField(max_length=1024)),
                ("url", models.CharField(blank=True, max_length=512)),
                ("sent_at", models.DateTimeField(auto_now_add=True)),
                (
                    "delivery_status",
                    models.CharField(
                        choices=[
                            ("delivered", "Delivered"),
                            ("failed", "Failed"),
                            ("skipped_disabled", "Skipped — type disabled"),
                            ("skipped_opted_out", "Skipped — user opted out"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pwa_notification_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "type",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="logs",
                        to="pwa_notifications.notificationtype",
                    ),
                ),
            ],
            options={"ordering": ["-sent_at"]},
        ),
        migrations.AddIndex(
            model_name="pushsubscription",
            index=models.Index(fields=["user", "is_active"], name="pwa_sub_user_active_idx"),
        ),
        migrations.AddIndex(
            model_name="notificationlog",
            index=models.Index(fields=["user", "sent_at"], name="pwa_log_user_sent_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="notificationpreference",
            unique_together={("user", "type")},
        ),
    ]
