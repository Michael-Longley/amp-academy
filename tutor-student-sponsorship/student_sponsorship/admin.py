from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Institution,
    InstitutionCourseAccess,
    InstitutionManager,
    Sponsorship,
    SponsorshipInvitation,
    TeacherStudentAssignment,
)


class InstitutionManagerInline(admin.TabularInline):
    model = InstitutionManager
    extra = 1
    fields = ["user", "role", "is_primary"]
    raw_id_fields = ["user"]


class InstitutionCourseAccessInline(admin.TabularInline):
    model = InstitutionCourseAccess
    extra = 1
    fields = ["course_id", "subsidy_pct"]


class SponsorshipInline(admin.TabularInline):
    model = Sponsorship
    extra = 0
    fields = ["invited_email", "student", "status", "sponsor_start", "grace_end"]
    readonly_fields = ["sponsor_start"]
    raw_id_fields = ["student"]
    show_change_link = True


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display  = ["name", "contact_email", "seat_limit", "seats_used_display",
                     "is_active", "contract_start", "contract_end"]
    list_filter   = ["is_active"]
    search_fields = ["name", "contact_email", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at", "seats_used_display"]
    inlines = [InstitutionManagerInline, InstitutionCourseAccessInline, SponsorshipInline]

    def seats_used_display(self, obj):
        used = obj.seats_used
        limit = obj.seat_limit
        if limit == 0:
            return format_html("<b>{}</b> / unlimited", used)
        color = "red" if used >= limit else "green"
        return format_html('<b style="color:{}">{}</b> / {}', color, used, limit)
    seats_used_display.short_description = "Seats used"


class TeacherStudentAssignmentInline(admin.TabularInline):
    model = TeacherStudentAssignment
    extra = 0
    fields = ["sponsorship", "assigned_at"]
    readonly_fields = ["assigned_at"]
    raw_id_fields = ["sponsorship"]


@admin.register(InstitutionManager)
class InstitutionManagerAdmin(admin.ModelAdmin):
    list_display  = ["user", "institution", "role", "is_primary", "created_at"]
    list_filter   = ["role", "institution"]
    search_fields = ["user__username", "user__email", "institution__name"]
    raw_id_fields = ["user"]
    inlines = [TeacherStudentAssignmentInline]


@admin.register(Sponsorship)
class SponsorshipAdmin(admin.ModelAdmin):
    list_display  = ["invited_email", "institution", "status",
                     "sponsor_start", "grace_end", "student_link"]
    list_filter   = ["status", "institution"]
    search_fields = ["invited_email", "student__username", "student__email"]
    readonly_fields = ["sponsor_start", "created_at", "updated_at"]
    raw_id_fields  = ["student", "removed_by"]

    def student_link(self, obj):
        if obj.student:
            url = f"/admin/auth/user/{obj.student.pk}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.student.username)
        return "—"
    student_link.short_description = "Student account"


@admin.register(SponsorshipInvitation)
class SponsorshipInvitationAdmin(admin.ModelAdmin):
    list_display  = ["sponsorship", "sent_at", "accepted_at", "expires_at",
                     "is_expired_display"]
    readonly_fields = ["token", "sent_at"]
    raw_id_fields   = ["sponsorship"]

    def is_expired_display(self, obj):
        return obj.is_expired
    is_expired_display.boolean = True
    is_expired_display.short_description = "Expired?"


@admin.register(InstitutionCourseAccess)
class InstitutionCourseAccessAdmin(admin.ModelAdmin):
    list_display  = ["institution", "course_id", "subsidy_pct", "added_at"]
    list_filter   = ["institution"]
    search_fields = ["course_id", "institution__name"]
