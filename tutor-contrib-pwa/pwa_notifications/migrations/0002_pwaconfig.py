from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pwa_notifications", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PwaConfig",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ("prompt_title", models.CharField(default="Stay in the loop", max_length=120)),
                ("prompt_body", models.TextField(default="Get notified about grades, upcoming assignments, and course announcements. You can turn these off anytime.")),
                ("prompt_accept", models.CharField(default="Turn on notifications", max_length=60)),
                ("prompt_decline", models.CharField(default="Not now", max_length=60)),
            ],
            options={
                "verbose_name": "PWA notification prompt",
                "verbose_name_plural": "PWA notification prompt",
            },
        ),
    ]
