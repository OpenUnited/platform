from django.apps import AppConfig


class TalentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "talent"

    def ready(self) -> None:
        import talent.signals
