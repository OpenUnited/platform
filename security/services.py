import logging
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from security.models import OrganisationPerson, Organisation, Person

from .models import User

logger = logging.getLogger(__name__)


class OrganisationPersonService:
    def __init__(self):
        pass

    def create(
        self, person_id: int, organisation_id: int, right: int
    ) -> tuple[OrganisationPerson, bool]:
        try:
            person = Person.objects.get(id=person_id)
            organisation = Organisation.objects.get(id=organisation_id)
            organisation_person = OrganisationPerson.objects.create(
                person=person, organisation=organisation, right=right
            )
            return organisation_person, True
        except Exception as e:
            logger.error(f"Failed to create OrganisationPerson due to: {e}")
            return None, False

    def update(
        self,
        organisation_person_id: int,
        person_id: int,
        organisation_id: int,
        right: int,
    ) -> tuple[OrganisationPerson, bool]:
        try:
            organisation_person = OrganisationPerson.objects.get(
                pk=organisation_person_id
            )
            person = Person.objects.get(id=person_id)
            organisation = Organisation.objects.get(id=organisation_id)

            organisation_person.person = person
            organisation_person.organisation = organisation
            organisation_person.right = right
            organisation_person.save()

            return organisation_person, True
        except OrganisationPerson.DoesNotExist as e:
            logger.error(f"Failed to update OrganisationPerson due to: {e}")
            return None, False

    def delete(self, organisation_person_id: int) -> bool:
        try:
            organisation_person = OrganisationPerson.objects.get(
                pk=organisation_person_id
            )
            organisation_person.delete()

            return True
        except OrganisationPerson.DoesNotExist as e:
            logger.error(f"Failed to delete OrganisationPerson due to: {e}")
            return False


class UserService:
    @transaction.atomic
    def create(
        self,
        username: str,
        email: str,
        password: str,
        is_active: bool,
        is_staff: bool,
        is_superuser: bool,
        is_logged: bool,
    ) -> User:
        user = User(
            username=username,
            email=email,
            password=password,
            is_active=is_active,
            is_staff=is_staff,
            is_superuser=is_superuser,
            is_logged=is_logged,
        )
        user.save()
        return user

    # Note that this method does not update the password.
    @transaction.atomic
    def update(
        self,
        username: str = None,
        email: str = None,
        password: str = None,
        is_active: bool = None,
        is_staff: bool = None,
        is_superuser: bool = None,
        is_logged: bool = None,
    ) -> User:
        try:
            user = User.objects.get(username=username)

            if username is not None:
                user.username = username
            if email is not None:
                user.email = email
            if is_active is not None:
                user.is_active = is_active
            if is_staff is not None:
                user.is_staff = is_staff
            if is_superuser is not None:
                user.is_superuser = is_superuser
            if is_logged is not None:
                user.is_logged = is_logged

            user.save()
            return user
        except User.DoesNotExist as e:
            logger.error(f"Failed to delete OrganisationPerson due to: {e}")
            return None

    def delete(self, username: str) -> bool:
        try:
            user = User.objects.get(username=username)
            user.delete()
            return True
        except User.DoesNotExist as e:
            logger.error(f"Failed to delete User due to: {e}")
            return False
