import os

from talent.models import Person, Skill, Expertise, Status
from openunited import settings


class StatusService:
    @staticmethod
    def create(**kwargs):
        status = Status(**kwargs)
        status.save()

        return status


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
    def get_initial_data(person: Person) -> dict:
        initial = {
            "full_name": person.full_name,
            "preferred_name": person.preferred_name,
            "headline": person.headline,
            "overview": person.overview,
            "github_link": person.github_link,
            "twitter_link": person.twitter_link,
            "linkedin_link": person.linkedin_link,
            "website_link": person.website_link,
            "send_me_bounties": person.send_me_bounties,
            "current_position": person.current_position,
        }
        return initial

    @staticmethod
    def does_require_upload(person: Person) -> [str, bool]:
        image_url = (
            settings.MEDIA_URL + settings.PERSON_PHOTO_UPLOAD_TO + "profile-empty.png"
        )
        requires_upload = True

        if person.photo:
            image_url = person.photo.url
            requires_upload = False

        return image_url, requires_upload

    @staticmethod
    def delete_photo(person: Person) -> None:
        path = person.photo.path
        if os.path.exists(path):
            os.remove(path)

        person.photo.delete(save=True)

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
