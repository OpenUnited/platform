from django.apps import AppConfig


class SecurityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.security"

    def ready(self) -> None:
        import apps.capabilities.security.signals
