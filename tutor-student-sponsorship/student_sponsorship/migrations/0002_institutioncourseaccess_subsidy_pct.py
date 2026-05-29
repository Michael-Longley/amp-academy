from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("student_sponsorship", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="institutioncourseaccess",
            name="subsidy_pct",
            field=models.DecimalField(
                decimal_places=2,
                default=100,
                help_text="Percentage of course cost covered by this institution (0–100).",
                max_digits=5,
            ),
        ),
    ]
