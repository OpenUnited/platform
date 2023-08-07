from django.contrib.auth import get_user_model
from random import randrange
from django.core.mail import send_mail

from talent.models import Person, Skill, Expertise
from security.models import SignUpRequest


Person = get_user_model()


class PersonService:
    @staticmethod
    def create(**kwargs):
        password = kwargs.pop("password", None)
        person = Person(**kwargs)
        if password:
            person.set_password(password)
        person.save()
        return person

    @staticmethod
    def get_by_id(id):
        person = Person.objects.get(id=id)
        return person

    @staticmethod
    def get_by_username(username: str) -> Person:
        return Person.objects.get(username=username)

    @staticmethod
    def update(person: Person, **kwargs):
        for key, value in kwargs.items():
            setattr(person, key, value)

        person.save()
        return person

    @staticmethod
    def delete(id):
        Person.objects.get(id=id).delete()

    @staticmethod
    def toggle_bounties(id):
        person = Person.objects.get(id=id)
        person.send_me_bounties = not person.send_me_bounties
        person.save()
        return person

    @staticmethod
    def make_test_user(id):
        person = Person.objects.get(id=id)
        person.is_test_user = True
        person.save()
        return person


class SkillService:
    @staticmethod
    def create(**kwargs):
        skill = Skill(**kwargs)
        skill.save()

        return skill


class ExpertiseService:
    @staticmethod
    def create(**kwargs):
        expertise = Expertise(**kwargs)
        expertise.save()

        return expertise


def create_and_send_verification_code(email: str) -> int:
    """
    Generate a random six-digit verification code, create a SignUpRequest object with
    the generated code, and send the code to the provided email address.

    Parameters:
        email (str): The email address to which the verification code will be sent.

    Returns:
        int: The ID of the created SignUpRequest object.
    """
    six_digit_number = randrange(100_000, 1_000_000)
    sign_up_request = SignUpRequest.objects.create(
        verification_code=str(six_digit_number)
    )

    send_mail(
        "Verification Code",
        f"Code: {six_digit_number}",
        None,
        [email],
    )

    return sign_up_request.id
