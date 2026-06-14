from django.apps import AppConfig


class PwaNotificationsConfig(AppConfig):
    name = "pwa_notifications"
    verbose_name = "PWA Push Notifications"

    plugin_app = {
        "url_config": {
            "lms.djangoapp": {
                "namespace": "pwa",
                "regex": "^api/pwa/",
                "relative_path": "urls",
            }
        }
    }

    def ready(self):
        import pwa_notifications.signals  # noqa: F401
