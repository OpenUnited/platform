from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Person, Status


@receiver(post_save, sender=Person)
def create_status_for_person(sender, instance, created, **kwargs):
    if created:
        _ = Status.objects.create(person=instance)
