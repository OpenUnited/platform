import logging
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from security.models import OrganisationPerson, Organisation, Person

from .models import ProductOwner

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


class ProductOwnerService:
    @staticmethod
    def create(**kwargs):
        product_owner = ProductOwner(**kwargs)
        product_owner.save()

        return product_owner
