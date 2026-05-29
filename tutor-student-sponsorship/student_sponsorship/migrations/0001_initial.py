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
            name="Institution",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("slug", models.SlugField(unique=True)),
                ("contact_name", models.CharField(blank=True, max_length=255)),
                ("contact_email", models.EmailField()),
                ("seat_limit", models.PositiveIntegerField(default=0, help_text="Maximum sponsored students. 0 = unlimited.")),
                ("is_active", models.BooleanField(default=True)),
                ("contract_start", models.DateField()),
                ("contract_end", models.DateField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="InstitutionManager",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ("role", models.CharField(choices=[("admin", "Admin"), ("teacher", "Teacher")], default="admin", max_length=20)),
                ("is_primary", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("institution", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="managers", to="student_sponsorship.institution")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="managed_institutions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"unique_together": {("institution", "user")}},
        ),
        migrations.CreateModel(
            name="Sponsorship",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ("invited_email", models.EmailField(help_text="Canonical email key. Survives user account deletion.")),
                ("status", models.CharField(choices=[("active", "Active"), ("pending", "Pending invitation"), ("grace", "Grace period"), ("expired", "Expired"), ("cancelled", "Cancelled")], db_index=True, default="active", max_length=20)),
                ("sponsor_start", models.DateField(auto_now_add=True)),
                ("grace_end", models.DateField(blank=True, help_text="Last day of access after sponsorship is removed.", null=True)),
                ("removed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("institution", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sponsorships", to="student_sponsorship.institution")),
                ("student", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sponsorships", to=settings.AUTH_USER_MODEL)),
                ("removed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="removed_sponsorships", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(
            model_name="sponsorship",
            index=models.Index(fields=["institution", "status"], name="student_spo_institu_idx"),
        ),
        migrations.AddIndex(
            model_name="sponsorship",
            index=models.Index(fields=["student", "status"], name="student_spo_student_idx"),
        ),
        migrations.AddConstraint(
            model_name="sponsorship",
            constraint=models.UniqueConstraint(
                condition=models.Q(status__in=["active", "pending", "grace"]),
                fields=["institution", "invited_email"],
                name="unique_active_sponsorship",
            ),
        ),
        migrations.CreateModel(
            name="SponsorshipInvitation",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ("token", models.UUIDField(db_index=True, default=uuid.uuid4, unique=True)),
                ("sent_at", models.DateTimeField(auto_now_add=True)),
                ("accepted_at", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateTimeField()),
                ("sponsorship", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="invitation", to="student_sponsorship.sponsorship")),
            ],
        ),
        migrations.CreateModel(
            name="InstitutionCourseAccess",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ("course_id", models.CharField(db_index=True, max_length=255)),
                ("added_at", models.DateTimeField(auto_now_add=True)),
                ("institution", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="course_access", to="student_sponsorship.institution")),
            ],
            options={
                "verbose_name": "Institution Course Access",
                "verbose_name_plural": "Institution Course Access",
                "unique_together": {("institution", "course_id")},
            },
        ),
        migrations.CreateModel(
            name="TeacherStudentAssignment",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                ("teacher", models.ForeignKey(
                    limit_choices_to={"role": "teacher"},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="student_assignments",
                    to="student_sponsorship.institutionmanager",
                )),
                ("sponsorship", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="teacher_assignments", to="student_sponsorship.sponsorship")),
            ],
            options={
                "verbose_name": "Teacher\u2013Student Assignment",
                "verbose_name_plural": "Teacher\u2013Student Assignments",
                "unique_together": {("teacher", "sponsorship")},
            },
        ),
    ]
