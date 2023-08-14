from django.contrib.auth.models import UserManager


class UserManager(UserManager):
    def get_or_none(self, **kwargs):
        try:
            return self.model.objects.get(**kwargs)
        except self.model.DoesNotExist:
            return None
