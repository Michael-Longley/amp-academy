from __future__ import annotations

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .access import admin_role_required, institution_required, resolve_viewable_sponsorships
from .emails import send_activation_email, send_invitation_email
from .forms import ClaimSponsorshipForm, CourseAccessForm, StudentAddForm, StudentEditForm, TeacherAddForm
from .models import (
    Institution,
    InstitutionCourseAccess,
    InstitutionManager,
    Sponsorship,
    SponsorshipInvitation,
    TeacherStudentAssignment,
)
from .progress import get_student_progress_summary
from .signals import _enroll_student

User = get_user_model()


# ── Portal home ───────────────────────────────────────────────────────────────

@login_required
def portal_home(request):
    if request.user.is_superuser:
        institutions = Institution.objects.all()
    else:
        institution_ids = InstitutionManager.objects.filter(
            user=request.user
        ).values_list("institution_id", flat=True)
        institutions = Institution.objects.filter(pk__in=institution_ids, is_active=True)

    if institutions.count() == 1:
        return redirect("sponsorship:student_list", institution_slug=institutions.first().slug)

    return render(request, "student_sponsorship/portal_home.html", {
        "institutions": institutions,
    })


# ── Student list ──────────────────────────────────────────────────────────────

@login_required
@institution_required
def student_list(request, institution_slug):
    institution = request.institution
    sponsorships = resolve_viewable_sponsorships(request, institution).order_by(
        "invited_email"
    )

    status_filter = request.GET.get("status", "")
    if status_filter:
        sponsorships = sponsorships.filter(status=status_filter)

    return render(request, "student_sponsorship/student_list.html", {
        "institution": institution,
        "sponsorships": sponsorships,
        "status_filter": status_filter,
        "status_choices": Sponsorship.STATUS_CHOICES,
        "manager": request.institution_manager,
    })


# ── Student add ───────────────────────────────────────────────────────────────

@login_required
@institution_required
@admin_role_required
def student_add(request, institution_slug):
    institution = request.institution
    form = StudentAddForm(
        request.POST or None,
        institution=institution,
    )
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        existing_user = User.objects.filter(email__iexact=email).first()
        sponsorship = Sponsorship.objects.create(
            institution=institution,
            student=existing_user,
            invited_email=email,
            status=Sponsorship.STATUS_ACTIVE if existing_user else Sponsorship.STATUS_PENDING,
        )
        if not existing_user:
            invitation = SponsorshipInvitation.objects.create(
                sponsorship=sponsorship,
                expires_at=timezone.now() + timedelta(days=7),
            )
            accept_url = request.build_absolute_uri(
                reverse("sponsorship:accept_invitation", args=[invitation.token])
            )
            send_invitation_email(sponsorship, invitation, accept_url)
            messages.success(
                request,
                f"Invitation sent to {email}. "
                "They'll receive an email with a link to accept their sponsorship.",
            )
        else:
            messages.success(request, f"{email} has been added as a sponsored student.")
        return redirect("sponsorship:student_list", institution_slug=institution_slug)

    return render(request, "student_sponsorship/student_add.html", {
        "institution": institution,
        "form": form,
    })


# ── Student detail ────────────────────────────────────────────────────────────

@login_required
@institution_required
def student_detail(request, institution_slug, pk):
    institution = request.institution
    viewable = resolve_viewable_sponsorships(request, institution)
    sponsorship = get_object_or_404(viewable, pk=pk)

    progress = {}
    if sponsorship.student:
        progress = get_student_progress_summary(sponsorship.student)

    invite_url = None
    if (
        sponsorship.status == Sponsorship.STATUS_PENDING
        and hasattr(sponsorship, "invitation")
        and not sponsorship.invitation.is_accepted
        and not sponsorship.invitation.is_expired
    ):
        invite_url = request.build_absolute_uri(
            reverse("sponsorship:accept_invitation", args=[sponsorship.invitation.token])
        )

    return render(request, "student_sponsorship/student_detail.html", {
        "institution": institution,
        "sponsorship": sponsorship,
        "progress": progress,
        "manager": request.institution_manager,
        "invite_url": invite_url,
    })


# ── Student edit ──────────────────────────────────────────────────────────────

@login_required
@institution_required
@admin_role_required
def student_edit(request, institution_slug, pk):
    institution = request.institution
    sponsorship = get_object_or_404(Sponsorship, pk=pk, institution=institution)
    form = StudentEditForm(request.POST or None, sponsorship=sponsorship)

    if request.method == "POST" and form.is_valid():
        new_email = form.cleaned_data["email"]
        old_email = sponsorship.invited_email
        sponsorship.invited_email = new_email

        new_user = User.objects.filter(email__iexact=new_email).first()
        sponsorship.student = new_user
        was_pending = sponsorship.status == Sponsorship.STATUS_PENDING
        if new_user and was_pending:
            sponsorship.status = Sponsorship.STATUS_ACTIVE

        sponsorship.save()
        if new_user and was_pending:
            _enroll_student(sponsorship)
        messages.success(
            request,
            f"Email updated from {old_email} to {new_email}.",
        )
        return redirect("sponsorship:student_detail", institution_slug=institution_slug, pk=pk)

    return render(request, "student_sponsorship/student_edit.html", {
        "institution": institution,
        "sponsorship": sponsorship,
        "form": form,
    })


# ── Student remove ────────────────────────────────────────────────────────────

@login_required
@institution_required
@admin_role_required
def student_remove(request, institution_slug, pk):
    institution = request.institution
    sponsorship = get_object_or_404(
        Sponsorship,
        pk=pk,
        institution=institution,
        status__in=[Sponsorship.STATUS_ACTIVE, Sponsorship.STATUS_PENDING],
    )

    if request.method == "POST":
        from django.conf import settings as django_settings
        grace_days = getattr(django_settings, "STUDENT_SPONSORSHIP_GRACE_DAYS", 0)
        sponsorship.begin_removal(removed_by_user=request.user, grace_days=grace_days)
        messages.success(
            request,
            f"Sponsorship for {sponsorship.invited_email} removed. "
            f"Access continues until {sponsorship.grace_end}.",
        )
        return redirect("sponsorship:student_list", institution_slug=institution_slug)

    return render(request, "student_sponsorship/student_remove_confirm.html", {
        "institution": institution,
        "sponsorship": sponsorship,
    })


# ── Institution courses ───────────────────────────────────────────────────────

@login_required
@institution_required
def institution_courses(request, institution_slug):
    institution = request.institution
    courses = InstitutionCourseAccess.objects.filter(
        institution=institution
    ).order_by("course_id")

    return render(request, "student_sponsorship/institution_courses.html", {
        "institution": institution,
        "courses": courses,
        "manager": request.institution_manager,
    })


@login_required
@institution_required
@admin_role_required
def course_add(request, institution_slug):
    institution = request.institution
    form = CourseAccessForm(
        request.POST or None,
        institution=institution,
    )

    if request.method == "POST" and form.is_valid():
        course_id = form.cleaned_data["course_id"]
        subsidy_pct = form.cleaned_data["subsidy_pct"]

        InstitutionCourseAccess.objects.create(
            institution=institution,
            course_id=course_id,
            subsidy_pct=subsidy_pct,
        )

        # Enroll all currently active/grace-period sponsored students in the new course.
        from .signals import _safe_enroll
        active_sponsorships = Sponsorship.objects.filter(
            institution=institution,
            status__in=[Sponsorship.STATUS_ACTIVE, Sponsorship.STATUS_GRACE],
        ).select_related("student")
        enrolled_count = 0
        for sp in active_sponsorships:
            if sp.student:
                _safe_enroll(sp.student, course_id)
                enrolled_count += 1

        msg = f"Course {course_id} added with {subsidy_pct}% subsidy."
        if enrolled_count:
            msg += f" {enrolled_count} existing student(s) enrolled."
        messages.success(request, msg)
        return redirect("sponsorship:institution_courses", institution_slug=institution_slug)

    return render(request, "student_sponsorship/course_add.html", {
        "institution": institution,
        "form": form,
    })


@login_required
@institution_required
@admin_role_required
def course_edit(request, institution_slug, pk):
    institution = request.institution
    ica = get_object_or_404(InstitutionCourseAccess, pk=pk, institution=institution)
    form = CourseAccessForm(
        request.POST or None,
        institution=institution,
        instance=ica,
    )

    if request.method == "POST" and form.is_valid():
        ica.subsidy_pct = form.cleaned_data["subsidy_pct"]
        ica.save(update_fields=["subsidy_pct"])
        messages.success(
            request,
            f"Subsidy for {ica.course_id} updated to {ica.subsidy_pct}%.",
        )
        return redirect("sponsorship:institution_courses", institution_slug=institution_slug)

    return render(request, "student_sponsorship/course_edit.html", {
        "institution": institution,
        "ica": ica,
        "form": form,
    })


@login_required
@institution_required
@admin_role_required
def course_remove(request, institution_slug, pk):
    institution = request.institution
    ica = get_object_or_404(InstitutionCourseAccess, pk=pk, institution=institution)

    if request.method == "POST":
        course_id = ica.course_id

        # Unenroll students whose only sponsored access to this course was via this institution.
        from .signals import _safe_unenroll
        active_sponsorships = Sponsorship.objects.filter(
            institution=institution,
            status__in=[Sponsorship.STATUS_ACTIVE, Sponsorship.STATUS_GRACE],
        ).select_related("student")

        unenrolled_count = 0
        for sp in active_sponsorships:
            if not sp.student:
                continue
            covered_elsewhere = InstitutionCourseAccess.objects.filter(
                course_id=course_id,
                institution__sponsorships__student=sp.student,
                institution__sponsorships__status__in=[
                    Sponsorship.STATUS_ACTIVE,
                    Sponsorship.STATUS_GRACE,
                ],
            ).exclude(institution=institution).exists()
            if not covered_elsewhere:
                _safe_unenroll(sp.student, course_id)
                unenrolled_count += 1

        ica.delete()

        msg = f"Course {course_id} removed from {institution.name}."
        if unenrolled_count:
            msg += f" {unenrolled_count} student(s) unenrolled."
        messages.success(request, msg)
        return redirect("sponsorship:institution_courses", institution_slug=institution_slug)

    return render(request, "student_sponsorship/course_remove_confirm.html", {
        "institution": institution,
        "ica": ica,
    })


# ── Teacher list ──────────────────────────────────────────────────────────────

@login_required
@institution_required
@admin_role_required
def teacher_list(request, institution_slug):
    institution = request.institution
    teachers = InstitutionManager.objects.filter(
        institution=institution,
        role=InstitutionManager.ROLE_TEACHER,
    ).select_related("user").prefetch_related("student_assignments__sponsorship")

    return render(request, "student_sponsorship/teacher_list.html", {
        "institution": institution,
        "teachers": teachers,
    })


# ── Teacher add ───────────────────────────────────────────────────────────────

@login_required
@institution_required
@admin_role_required
def teacher_add(request, institution_slug):
    institution = request.institution
    form = TeacherAddForm(request.POST or None, institution=institution)

    if request.method == "POST" and form.is_valid():
        user = form.cleaned_data["_user"]
        InstitutionManager.objects.create(
            institution=institution,
            user=user,
            role=InstitutionManager.ROLE_TEACHER,
        )
        messages.success(request, f"{user.email} added as a teacher.")
        return redirect("sponsorship:teacher_list", institution_slug=institution_slug)

    return render(request, "student_sponsorship/teacher_add.html", {
        "institution": institution,
        "form": form,
    })


# ── Teacher assign students ───────────────────────────────────────────────────

@login_required
@institution_required
@admin_role_required
def teacher_assign(request, institution_slug, teacher_pk):
    institution = request.institution
    teacher = get_object_or_404(
        InstitutionManager,
        pk=teacher_pk,
        institution=institution,
        role=InstitutionManager.ROLE_TEACHER,
    )
    all_sponsorships = Sponsorship.objects.filter(
        institution=institution,
        status__in=[Sponsorship.STATUS_ACTIVE, Sponsorship.STATUS_PENDING, Sponsorship.STATUS_GRACE],
    ).order_by("invited_email")

    assigned_ids = set(
        teacher.student_assignments.values_list("sponsorship_id", flat=True)
    )

    if request.method == "POST":
        selected_ids = set(int(x) for x in request.POST.getlist("sponsorships"))
        to_add    = selected_ids - assigned_ids
        to_remove = assigned_ids - selected_ids

        TeacherStudentAssignment.objects.filter(
            teacher=teacher, sponsorship_id__in=to_remove
        ).delete()
        TeacherStudentAssignment.objects.bulk_create([
            TeacherStudentAssignment(teacher=teacher, sponsorship_id=sid)
            for sid in to_add
        ])
        messages.success(request, f"Student assignments updated for {teacher.user.email}.")
        return redirect("sponsorship:teacher_list", institution_slug=institution_slug)

    return render(request, "student_sponsorship/teacher_assign.html", {
        "institution": institution,
        "teacher": teacher,
        "all_sponsorships": all_sponsorships,
        "assigned_ids": assigned_ids,
    })


# ── Accept invitation (token-based) ──────────────────────────────────────────

def accept_invitation(request, token):
    invitation = get_object_or_404(SponsorshipInvitation, token=token)

    if invitation.is_accepted:
        messages.info(request, "This invitation has already been accepted.")
        return redirect("sponsorship:portal_home")

    if invitation.is_expired:
        messages.error(request, "This invitation link has expired. Contact your institution.")
        return redirect("sponsorship:portal_home")

    if not request.user.is_authenticated:
        from django.conf import settings as django_settings
        login_url = getattr(django_settings, "LOGIN_URL", "/login")
        return redirect(f"{login_url}?next={request.path}")

    sponsorship = invitation.sponsorship
    sponsorship.student = request.user
    sponsorship.invited_email = request.user.email
    sponsorship.status = Sponsorship.STATUS_ACTIVE
    sponsorship.save()
    _enroll_student(sponsorship)

    invitation.accepted_at = timezone.now()
    invitation.save()

    send_activation_email(sponsorship)

    messages.success(
        request,
        f"You are now sponsored by {sponsorship.institution.name}. "
        "Your courses have been enrolled.",
    )
    return redirect("/dashboard")


# ── Claim sponsorship (self-enrollment for existing accounts) ─────────────────

@login_required
def claim_sponsorship(request):
    form = ClaimSponsorshipForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].lower().strip()

        if email != request.user.email.lower():
            messages.error(
                request,
                "The email you entered doesn't match your account email. "
                "Contact your institution to update the sponsorship email.",
            )
            return render(request, "student_sponsorship/claim_sponsorship.html", {
                "form": form,
            })

        sponsorship = Sponsorship.objects.filter(
            invited_email__iexact=email,
            status=Sponsorship.STATUS_PENDING,
        ).first()

        if not sponsorship:
            messages.error(
                request,
                "No pending sponsorship found for this email. "
                "Check with your institution or contact Amp Academy support.",
            )
            return render(request, "student_sponsorship/claim_sponsorship.html", {
                "form": form,
            })

        sponsorship.student = request.user
        sponsorship.status = Sponsorship.STATUS_ACTIVE
        sponsorship.save()
        _enroll_student(sponsorship)

        if hasattr(sponsorship, "invitation"):
            sponsorship.invitation.accepted_at = timezone.now()
            sponsorship.invitation.save()

        send_activation_email(sponsorship)

        messages.success(
            request,
            f"Sponsorship from {sponsorship.institution.name} linked to your account. "
            "Your courses have been enrolled.",
        )
        return redirect("/dashboard")

    return render(request, "student_sponsorship/claim_sponsorship.html", {
        "form": form,
    })
