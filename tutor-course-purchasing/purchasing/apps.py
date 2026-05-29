from django.apps import AppConfig


class PurchasingConfig(AppConfig):
    name = "purchasing"
    verbose_name = "Course Purchasing"

    plugin_app = {
        "url_config": {
            "lms.djangoapp": {
                "namespace": "purchasing",
                "regex": "^purchasing/",
                "relative_path": "urls",
            }
        }
    }

    def ready(self):
        import purchasing.signals  # noqa: F401
