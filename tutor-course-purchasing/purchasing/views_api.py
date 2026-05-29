from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .access import has_access
from .models import CoursePrice, Order, Subscription
from .serializers import CoursePriceSerializer, OrderSerializer, SubscriptionSerializer


@api_view(["GET"])
def course_price(request, course_id):
    try:
        price = CoursePrice.objects.get(course_id=course_id, is_active=True)
    except CoursePrice.DoesNotExist:
        return Response({"detail": "No pricing found for this course."}, status=status.HTTP_404_NOT_FOUND)
    return Response(CoursePriceSerializer(price).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def course_access(request, course_id):
    return Response({"has_access": has_access(request.user, course_id)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_list(request):
    qs = Order.objects.filter(user=request.user).order_by("-created_at")
    return Response(OrderSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def subscription_list(request):
    qs = Subscription.objects.filter(
        user=request.user
    ).exclude(status=Subscription.STATUS_EXPIRED).order_by("-created_at")
    return Response(SubscriptionSerializer(qs, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def subscription_cancel(request, subscription_id):
    sub = get_object_or_404(Subscription, id=subscription_id, user=request.user)
    if sub.status not in (
        Subscription.STATUS_ACTIVE,
        Subscription.STATUS_PAST_DUE,
        Subscription.STATUS_GRACE_PERIOD,
    ):
        return Response({"detail": "Subscription cannot be cancelled."}, status=status.HTTP_400_BAD_REQUEST)

    from .access import get_processor
    from .models import CourseAccess
    from . import enrollment
    from django.utils import timezone

    processor = get_processor()
    processor.cancel_subscription(sub)
    sub.status = Subscription.STATUS_CANCELLED
    sub.cancelled_at = timezone.now()
    sub.save(update_fields=["status", "cancelled_at"])
    CourseAccess.objects.filter(subscription=sub).update(is_active=False)
    enrollment.unenroll_user(request.user, sub.course_id)

    return Response(SubscriptionSerializer(sub).data)
