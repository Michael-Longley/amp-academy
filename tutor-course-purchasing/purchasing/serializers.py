from rest_framework import serializers

from .models import CourseAccess, CoursePrice, Order, Subscription


class CoursePriceSerializer(serializers.ModelSerializer):
    offers_one_time = serializers.BooleanField(read_only=True)
    offers_subscription = serializers.BooleanField(read_only=True)
    is_free = serializers.BooleanField(read_only=True)

    class Meta:
        model = CoursePrice
        fields = [
            "course_id",
            "pricing_options",
            "one_time_price_usd",
            "subscription_price_usd",
            "is_free",
            "offers_one_time",
            "offers_subscription",
            "is_active",
        ]


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "id",
            "course_id",
            "order_type",
            "amount_usd",
            "status",
            "processor_name",
            "created_at",
            "completed_at",
            "refunded_at",
        ]
        read_only_fields = fields


class SubscriptionSerializer(serializers.ModelSerializer):
    is_accessible = serializers.BooleanField(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "course_id",
            "status",
            "current_period_end",
            "grace_period_end",
            "cancelled_at",
            "created_at",
            "is_accessible",
        ]
        read_only_fields = fields
