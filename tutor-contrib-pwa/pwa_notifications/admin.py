from django.contrib import admin

from pwa_notifications.models import NotificationLog, NotificationPreference, NotificationType, PushSubscription, PwaConfig


@admin.register(PwaConfig)
class PwaConfigAdmin(admin.ModelAdmin):
    fields = ["prompt_title", "prompt_body", "prompt_accept", "prompt_decline"]

    def has_add_permission(self, request):
        return not PwaConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Redirect straight to the edit form — there's only ever one row
        obj = PwaConfig.load()
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        return HttpResponseRedirect(
            reverse("admin:pwa_notifications_pwaconfig_change", args=[obj.pk])
        )


@admin.register(NotificationType)
class NotificationTypeAdmin(admin.ModelAdmin):
    list_display = ["id", "label", "enabled", "created_at"]
    list_editable = ["enabled"]
    search_fields = ["id", "label"]
    ordering = ["id"]


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "is_active", "user_agent", "created_at", "last_seen"]
    list_filter = ["is_active"]
    search_fields = ["user__username", "endpoint"]
    readonly_fields = ["user", "endpoint", "p256dh", "auth", "user_agent", "created_at", "last_seen"]
    ordering = ["-last_seen"]


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ["user", "type", "enabled"]
    list_filter = ["type", "enabled"]
    search_fields = ["user__username"]
    readonly_fields = ["user", "type"]


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ["user", "type", "title", "delivery_status", "sent_at"]
    list_filter = ["delivery_status", "type"]
    search_fields = ["user__username", "title"]
    readonly_fields = ["user", "type", "title", "body", "url", "sent_at", "delivery_status"]
    ordering = ["-sent_at"]
