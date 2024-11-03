from django.contrib.auth.models import UserManager
from django.db.models import Q


class UserManager(UserManager):
    def get_or_none(self, **kwargs):
        try:
            return self.model.objects.get(**kwargs)
        except self.model.DoesNotExist:
            return None

    def get_user_by_username_or_email(self, username):
        try:
            user = self.model.objects.get(Q(username__exact=username) | Q(email__exact=username))
        # This shouldn't happen. It is written just in case
        except self.model.MultipleObjectsReturned:
            user = (
                self.model.objects.filter(Q(username__exact=username) | Q(email__exact=username))
                .order_by("id")
                .first()
            )
        except self.model.DoesNotExist:
            return None

        return user
