"""Portal access control helpers."""
from __future__ import annotations

from functools import wraps

from django.conf import settings
from django.shortcuts import redirect

from .models import InstitutionManager, Sponsorship


def resolve_manager(user, institution):
    """Return InstitutionManager for user+institution, or None."""
    if user.is_superuser:
        return None
    try:
        return InstitutionManager.objects.select_related("institution").get(
            user=user,
            institution=institution,
            institution__is_active=True,
        )
    except InstitutionManager.DoesNotExist:
        return False


def resolve_viewable_sponsorships(request, institution):
    """Return the Sponsorship queryset this user is allowed to read."""
    qs = Sponsorship.objects.filter(institution=institution).select_related("student")
    if request.user.is_superuser:
        return qs
    manager = getattr(request, "institution_manager", None)
    if manager is None or manager.is_admin:
        return qs
    assigned_ids = manager.student_assignments.values_list("sponsorship_id", flat=True)
    return qs.filter(pk__in=assigned_ids)


def institution_required(view_func):
    """Gate a view to institution managers only. Sets request.institution_manager."""
    @wraps(view_func)
    def wrapper(request, institution_slug, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = getattr(settings, "LOGIN_URL", "/login")
            return redirect(f"{login_url}?next={request.path}")

        if request.user.is_superuser:
            from .models import Institution
            try:
                institution = Institution.objects.get(slug=institution_slug)
            except Institution.DoesNotExist:
                return redirect("sponsorship:portal_home")
            request.institution = institution
            request.institution_manager = None
            return view_func(request, institution_slug, *args, **kwargs)

        try:
            mgr = InstitutionManager.objects.select_related("institution").get(
                user=request.user,
                institution__slug=institution_slug,
                institution__is_active=True,
            )
        except InstitutionManager.DoesNotExist:
            return redirect("sponsorship:portal_home")

        request.institution = mgr.institution
        request.institution_manager = mgr
        return view_func(request, institution_slug, *args, **kwargs)

    return wrapper


def admin_role_required(view_func):
    """Must be used after @institution_required. Rejects teachers with 403."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        mgr = getattr(request, "institution_manager", None)
        if mgr is not None and mgr.is_teacher:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Teachers do not have permission for this action.")
        return view_func(request, *args, **kwargs)
    return wrapper
