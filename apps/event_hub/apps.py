from django.apps import AppConfig

class EventHubConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.event_hub'

    def ready(self):
        # Import any signal handlers or event listeners here
        pass
