import uuid
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CoursePrice",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("course_id", models.CharField(db_index=True, max_length=255, unique=True)),
                ("one_time_price_usd", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, help_text="Leave blank if one-time purchase is not offered.")),
                ("subscription_price_usd", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, help_text="Monthly subscription price. Leave blank if subscription is not offered.")),
                ("pricing_options", models.CharField(choices=[("free", "Free"), ("one_time", "One-time purchase"), ("subscription", "Subscription only"), ("both", "One-time & Subscription")], default="one_time", max_length=20)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Course Price",
                "verbose_name_plural": "Course Prices",
                "ordering": ["course_id"],
            },
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("course_id", models.CharField(db_index=True, max_length=255)),
                ("order_type", models.CharField(choices=[("one_time", "One-time purchase"), ("subscription_start", "Subscription start")], max_length=30)),
                ("amount_usd", models.DecimalField(decimal_places=2, max_digits=10)),
                ("writer_share_usd", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("platform_share_usd", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("writer_user_id_snapshot", models.IntegerField(blank=True, null=True, help_text="Snapshot of writer user ID at purchase time for future payout reference.")),
                ("processor_name", models.CharField(default="stub", max_length=50)),
                ("processor_session_id", models.CharField(blank=True, max_length=255)),
                ("processor_order_id", models.CharField(blank=True, max_length=255)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("complete", "Complete"), ("failed", "Failed"), ("refunded", "Refunded")], db_index=True, default="pending", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("refunded_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="purchasing_orders", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Order",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Subscription",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("course_id", models.CharField(db_index=True, max_length=255)),
                ("processor_name", models.CharField(default="stub", max_length=50)),
                ("processor_subscription_id", models.CharField(blank=True, max_length=255)),
                ("status", models.CharField(choices=[("active", "Active"), ("past_due", "Past due"), ("grace_period", "Grace period"), ("cancelled", "Cancelled"), ("expired", "Expired")], db_index=True, default="active", max_length=20)),
                ("current_period_end", models.DateTimeField()),
                ("grace_period_end", models.DateTimeField(blank=True, null=True)),
                ("cancelled_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="purchasing_subscriptions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Subscription",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="CourseAccess",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("course_id", models.CharField(db_index=True, max_length=255)),
                ("access_type", models.CharField(choices=[("one_time", "One-time purchase (lifetime)"), ("subscription", "Subscription"), ("free", "Free course"), ("sponsorship", "Institutional sponsorship")], max_length=20)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True, help_text="Null = lifetime access (one_time, free). Set for subscriptions in grace period.")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("order", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="accesses", to="purchasing.order")),
                ("subscription", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="accesses", to="purchasing.subscription")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="course_accesses", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Course Access",
                "verbose_name_plural": "Course Accesses",
            },
        ),
        migrations.AddIndex(
            model_name="courseaccess",
            index=models.Index(fields=["user", "course_id", "is_active"], name="purchasing__user_id_29a0a5_idx"),
        ),
        migrations.CreateModel(
            name="RevenueSplit",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("course_id", models.CharField(blank=True, db_index=True, max_length=255, null=True, help_text="Leave blank for the global platform default.")),
                ("writer_share_pct", models.DecimalField(decimal_places=2, max_digits=5, help_text="Writer's share as a percentage (e.g. 70.00).")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("set_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="revenue_splits_configured", to=settings.AUTH_USER_MODEL)),
                ("writer_user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="revenue_splits", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Revenue Split",
                "verbose_name_plural": "Revenue Splits",
            },
        ),
    ]
