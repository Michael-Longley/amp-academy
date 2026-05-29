import re
from datetime import date, timedelta

from django import forms
from django.utils import timezone

from .models import Institution, InstitutionCourseAccess, InstitutionManager, Sponsorship

COURSE_ID_RE = re.compile(r"^course-v1:[^/+]+\+[^/+]+\+[^/+]+$")


class StudentAddForm(forms.Form):
    email = forms.EmailField(
        label="Student email",
        widget=forms.EmailInput(attrs={"placeholder": "student@example.com", "class": "form-control"}),
    )

    def __init__(self, *args, institution=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.institution = institution

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if self.institution:
            # Reject if the institution's contract has expired.
            if self.institution.contract_end and self.institution.contract_end < date.today():
                raise forms.ValidationError(
                    f"This institution's contract expired on "
                    f"{self.institution.contract_end.strftime('%B %d, %Y')}. "
                    "Contact Amp Academy to renew before adding students."
                )
            exists = Sponsorship.objects.filter(
                institution=self.institution,
                invited_email=email,
                status__in=[
                    Sponsorship.STATUS_ACTIVE,
                    Sponsorship.STATUS_PENDING,
                    Sponsorship.STATUS_GRACE,
                ],
            ).exists()
            if exists:
                raise forms.ValidationError(
                    "This student already has an active sponsorship with your institution."
                )
            limit = self.institution.seat_limit
            if limit > 0 and self.institution.seats_used >= limit:
                raise forms.ValidationError(
                    f"Seat limit reached ({limit}). "
                    "Contact Amp Academy to expand your contract."
                )
        return email


class StudentEditForm(forms.Form):
    email = forms.EmailField(
        label="New email address",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, sponsorship=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.sponsorship = sponsorship
        if sponsorship:
            self.fields["email"].initial = sponsorship.invited_email

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if self.sponsorship:
            conflict = Sponsorship.objects.filter(
                institution=self.sponsorship.institution,
                invited_email=email,
                status__in=[
                    Sponsorship.STATUS_ACTIVE,
                    Sponsorship.STATUS_PENDING,
                    Sponsorship.STATUS_GRACE,
                ],
            ).exclude(pk=self.sponsorship.pk).exists()
            if conflict:
                raise forms.ValidationError(
                    "Another active sponsorship already uses this email."
                )
        return email


class TeacherAddForm(forms.Form):
    email = forms.EmailField(
        label="Teacher email",
        help_text="Must be an existing LMS account.",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, institution=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.institution = institution

    def clean_email(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        email = self.cleaned_data["email"].lower().strip()
        try:
            self.cleaned_data["_user"] = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise forms.ValidationError(
                "No LMS account found with this email. "
                "The teacher must register first."
            )
        if self.institution:
            if InstitutionManager.objects.filter(
                institution=self.institution,
                user=self.cleaned_data["_user"],
            ).exists():
                raise forms.ValidationError(
                    "This user is already a manager or teacher for this institution."
                )
        return email


class ClaimSponsorshipForm(forms.Form):
    email = forms.EmailField(
        label="Sponsorship email",
        help_text="Enter the email address your institution used to sponsor you.",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )


class CourseAccessForm(forms.Form):
    course_id = forms.CharField(
        label="Course ID",
        max_length=255,
        help_text="Open edX format: course-v1:Org+Course+Run",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "course-v1:AmpAcademy+ELE101+2025",
        }),
    )
    subsidy_pct = forms.DecimalField(
        label="Subsidy percentage",
        min_value=0,
        max_value=100,
        decimal_places=2,
        initial=100,
        help_text="Portion of the course price covered by this institution (0–100). "
                  "100 = fully sponsored; 50 = half price.",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )

    def __init__(self, *args, institution=None, instance=None, **kwargs):
        """
        institution  — Institution being edited (used to check duplicates on add).
        instance     — Existing InstitutionCourseAccess row (edit mode: locks course_id).
        """
        super().__init__(*args, **kwargs)
        self.institution = institution
        self.instance = instance
        if instance:
            self.fields["course_id"].initial = instance.course_id
            self.fields["course_id"].disabled = True   # course_id is immutable on edit
            self.fields["subsidy_pct"].initial = instance.subsidy_pct

    def clean_course_id(self):
        course_id = self.cleaned_data["course_id"].strip()
        if not COURSE_ID_RE.match(course_id):
            raise forms.ValidationError(
                "Must be in Open edX format: course-v1:Org+Course+Run"
            )
        # On add, reject duplicates for this institution.
        if self.institution and not self.instance:
            if InstitutionCourseAccess.objects.filter(
                institution=self.institution,
                course_id=course_id,
            ).exists():
                raise forms.ValidationError(
                    "This course is already in the institution's access list."
                )
        return course_id
