from django.contrib import admin

from .models import CourseAccess, CoursePrice, Order, RevenueSplit, Subscription
from . import signals as purchasing_signals


@admin.register(CoursePrice)
class CoursePriceAdmin(admin.ModelAdmin):
    list_display = ("course_id", "pricing_options", "one_time_price_usd", "subscription_price_usd", "is_active")
    list_filter = ("pricing_options", "is_active")
    search_fields = ("course_id",)
    list_editable = ("is_active",)


@admin.register(RevenueSplit)
class RevenueSplitAdmin(admin.ModelAdmin):
    list_display = ("course_id", "writer_user", "writer_share_pct", "platform_share_pct", "set_by", "created_at")
    search_fields = ("course_id", "writer_user__username")
    readonly_fields = ("set_by", "created_at", "platform_share_pct")

    def save_model(self, request, obj, form, change):
        if not obj.set_by_id:
            obj.set_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description="Platform %")
    def platform_share_pct(self, obj):
        return f"{obj.platform_share_pct:.2f}%"


@admin.action(description="Issue refund for selected orders")
def refund_orders(modeladmin, request, queryset):
    for order in queryset.filter(status=Order.STATUS_COMPLETE):
        purchasing_signals.revoke_order(order)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "course_id", "order_type", "amount_usd", "status", "created_at", "completed_at")
    list_filter = ("status", "order_type", "processor_name")
    search_fields = ("user__username", "course_id", "processor_order_id")
    readonly_fields = ("id", "created_at", "completed_at", "refunded_at")
    actions = [refund_orders]
    ordering = ["-created_at"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "course_id", "status", "current_period_end", "created_at")
    list_filter = ("status", "processor_name")
    search_fields = ("user__username", "course_id", "processor_subscription_id")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ["-created_at"]


@admin.register(CourseAccess)
class CourseAccessAdmin(admin.ModelAdmin):
    list_display = ("user", "course_id", "access_type", "is_active", "expires_at", "created_at")
    list_filter = ("access_type", "is_active")
    search_fields = ("user__username", "course_id")
    readonly_fields = ("created_at",)
    list_editable = ("is_active",)
