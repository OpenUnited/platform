from django.apps import AppConfig

class ChallengeAuthoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.flows.challenge_authoring'
    label = 'challenge_authoring'
    verbose_name = 'Challenge Authoring Flow'