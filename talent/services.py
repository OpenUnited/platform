import os
from urllib.parse import urlparse
from django.db.models import Count, Avg


from .models import (
    Person,
    Skill,
    Expertise,
    Status,
    PersonSkill,
    BountyClaim,
    Feedback,
)
from openunited.settings.base import MEDIA_URL, PERSON_PHOTO_UPLOAD_TO


class StatusService:
    @staticmethod
    def create(**kwargs):
        status = Status(**kwargs)
        status.save()

        return status

    @staticmethod
    def get_privileges(status: str) -> str:
        return Status.STATUS_PRIVILEGES_MAPPING.get(status)

    @staticmethod
    def get_statuses() -> list:
        return list(Status.STATUS_POINT_MAPPING.keys())

    @staticmethod
    def get_display_points(status: str) -> str:
        statuses = StatusService.get_statuses()

        # if `status` is the last one in `statuses`
        if status == statuses[-1]:
            return f">= {StatusService.get_points_for_status(status)}"

        # +1 is to get the next status
        index = statuses.index(status) + 1
        return f"< {StatusService.get_points_for_status(statuses[index])}"

    @staticmethod
    def get_points_for_status(status: str) -> str:
        return Status.STATUS_POINT_MAPPING.get(status)


class StatusService:
    @staticmethod
    def create(**kwargs):
        status = Status(**kwargs)
        status.save()

        return status

    @staticmethod
    def get_privileges(status: str) -> str:
        return Status.STATUS_PRIVILEGES_MAPPING.get(status)

    @staticmethod
    def get_statuses() -> list:
        return list(Status.STATUS_POINT_MAPPING.keys())

    @staticmethod
    def get_display_points(status: str) -> str:
        statuses = StatusService.get_statuses()

        # if `status` is the last one in `statuses`
        if status == statuses[-1]:
            return f">= {StatusService.get_points_for_status(status)}"

        # +1 is to get the next status
        index = statuses.index(status) + 1
        return f"< {StatusService.get_points_for_status(statuses[index])}"

    @staticmethod
    def get_points_for_status(status: str) -> str:
        return Status.STATUS_POINT_MAPPING.get(status)


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
            "location": person.location,
        }
        return initial

    @staticmethod
    def get_path_from_url(url_string):
        parsed = urlparse(url_string)
        return parsed.path.strip("/")

    @staticmethod
    def get_photo_url(person: Person) -> [str, bool]:
        image_url = MEDIA_URL + PERSON_PHOTO_UPLOAD_TO + "profile-empty.png"
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


class PersonSkillService:
    @staticmethod
    def create(**kwargs):
        person_skill = PersonSkill(**kwargs)
        person_skill.save()

        return person_skill


class BountyClaimService:
    @staticmethod
    def create(**kwargs):
        bounty_claim = BountyClaim(**kwargs)
        bounty_claim.save()

        return bounty_claim


class FeedbackService:
    @staticmethod
    def get_analytics_for_person(person: Person) -> dict:
        feedbacks = Feedback.objects.filter(recipient=person)

        total_feedbacks = feedbacks.count()

        feedback_aggregates = feedbacks.aggregate(
            feedback_count=Count("id"), average_stars=Avg("stars")
        )

        # Calculate percentages
        feedback_aggregates["average_stars"] = (
            int(round(feedback_aggregates["average_stars"], 2))
            if feedback_aggregates["average_stars"] is not None
            else None
        )

        stars_counts = feedbacks.values("stars").annotate(count=Count("id"))

        stars_percentages = {
            star: int(round(0 / total_feedbacks * 100, 2)) for star in range(1, 6)
        }

        for entry in stars_counts:
            stars_percentages[entry["stars"]] = int(
                round(entry["count"] / total_feedbacks * 100, 2)
            )

        feedback_aggregates.update(stars_percentages)

        return feedback_aggregates
