import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from pwa_notifications.models import NotificationPreference, NotificationType, PushSubscription


@login_required
@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def subscribe(request):
    if request.method == "POST":
        return _subscribe(request)
    return _unsubscribe(request)


def _subscribe(request):
    try:
        payload = json.loads(request.body)
        endpoint = payload["endpoint"]
        keys = payload["keys"]
        p256dh = keys["p256dh"]
        auth = keys["auth"]
    except (KeyError, ValueError):
        return JsonResponse({"error": "Invalid subscription payload."}, status=400)

    user_agent = request.META.get("HTTP_USER_AGENT", "")[:512]

    sub, created = PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={
            "user": request.user,
            "p256dh": p256dh,
            "auth": auth,
            "user_agent": user_agent,
            "is_active": True,
        },
    )
    status = 201 if created else 200
    return JsonResponse({"id": sub.pk}, status=status)


def _unsubscribe(request):
    try:
        payload = json.loads(request.body)
        endpoint = payload["endpoint"]
    except (KeyError, ValueError):
        return JsonResponse({"error": "Invalid payload."}, status=400)

    PushSubscription.objects.filter(
        user=request.user, endpoint=endpoint
    ).update(is_active=False)
    return JsonResponse({}, status=204)


@login_required
@require_http_methods(["GET", "POST"])
def notification_preferences(request):
    if request.method == "GET":
        return _get_preferences(request)
    return _set_preference(request)


def _get_preferences(request):
    types = NotificationType.objects.filter(enabled=True)
    prefs = {
        p.type_id: p.enabled
        for p in NotificationPreference.objects.filter(user=request.user)
    }
    data = [
        {
            "type_id": t.id,
            "label": t.label,
            "description": t.description,
            "enabled": prefs.get(t.id, True),
        }
        for t in types
    ]
    return JsonResponse({"preferences": data})


def _set_preference(request):
    try:
        payload = json.loads(request.body)
        type_id = payload["type_id"]
        enabled = bool(payload["enabled"])
    except (KeyError, ValueError):
        return JsonResponse({"error": "Invalid payload."}, status=400)

    try:
        ntype = NotificationType.objects.get(pk=type_id)
    except NotificationType.DoesNotExist:
        return JsonResponse({"error": "Unknown notification type."}, status=404)

    NotificationPreference.objects.update_or_create(
        user=request.user,
        type=ntype,
        defaults={"enabled": enabled},
    )
    return JsonResponse({"type_id": type_id, "enabled": enabled})
