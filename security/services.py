import logging
from django.core.exceptions import ObjectDoesNotExist
from security.models import OrganisationPerson, Organisation, Person

logger = logging.getLogger(__name__)

class OrganisationPersonService:
    def create(person_id, organisation_id, right):
        try:
            person = Person.objects.get(id=person_id)
            organisation = Organisation.objects.get(id=organisation_id)
            organisation_person = OrganisationPerson.objects.create(
                person=person, 
                organisation=organisation, 
                right=right
            )
            return organisation_person, True
        except Exception as e:
            logger.error(f"Failed to create OrganisationPerson due to: {e}")
            return None, False

    def update(organisation_person_id, person_id, organisation_id, right):
        try:
            organisation_person = OrganisationPerson.objects.get(pk=organisation_person_id)
            person = Person.objects.get(id=person_id)
            organisation = Organisation.objects.get(id=organisation_id)

            organisation_person.person = person
            organisation_person.organisation = organisation
            organisation_person.right = right
            organisation_person.save()

            return organisation_person, True
        except ObjectDoesNotExist as e:
            logger.error(f"Failed to update OrganisationPerson due to: {e}")
            return None, False

    def delete(organisation_person_id):
        try:
            organisation_person = OrganisationPerson.objects.get(pk=organisation_person_id)
            organisation_person.delete()

            return True
        except ObjectDoesNotExist as e:
            logger.error(f"Failed to delete OrganisationPerson due to: {e}")
            return False
