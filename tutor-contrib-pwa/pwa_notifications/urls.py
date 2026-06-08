from django.urls import path

from pwa_notifications import views

app_name = "pwa"

urlpatterns = [
    path("subscribe/", views.subscribe, name="subscribe"),
    path("notification-preferences/", views.notification_preferences, name="notification_preferences"),
]
