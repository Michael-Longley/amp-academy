from django.apps import AppConfig


class StudentSponsorshipConfig(AppConfig):
    name = "student_sponsorship"
    verbose_name = "Student Sponsorship"

    plugin_app = {
        "url_config": {
            "lms.djangoapp": {
                "namespace": "sponsorship",
                "regex": "^sponsorship/",
                "relative_path": "urls",
            }
        }
    }

    def ready(self):
        import student_sponsorship.signals  # noqa: F401
