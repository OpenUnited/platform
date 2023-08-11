from django.dispatch.dispatcher import receiver
from django.db.models.signals import pre_save

from .models import User


@receiver(pre_save, sender=User)
def pre_save_receiver(sender, instance, **kwargs):
    """
    The function checks if the password of a user instance has been changed and updates some fields
    accordingly.

    :param sender: The `sender` parameter in this context refers to the model class that is sending the
    signal. In this case, it is the `User` model
    :param instance: The `instance` parameter refers to the instance of the model that is being saved.
    In this case, it refers to an instance of the `User` model
    :return: In this code snippet, the `pre_save_receiver` function is returning `None` if the
    `old_user` is `None`.
    """
    old_user = User.objects.get_or_none(pk=instance.pk)
    if old_user is None:
        return

    if instance.password != old_user.password:
        instance.remaining_budget_for_failed_logins = 3
        instance.password_reset_required = False
