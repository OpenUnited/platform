import uuid

from django.forms.models import model_to_dict


def get_person_data(person):
    return {"first_name": person.first_name, "username": person.user.username}


def to_dict(instance):
    result = model_to_dict(instance)
    return {key: str(result[key]) if isinstance(result[key], uuid.UUID) else result[key] for key in result.keys()}
