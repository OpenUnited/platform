import logging
from django.core.exceptions import ValidationError

from .models import ProductPerson, ProductOwner

logger = logging.getLogger(__name__)


class ProductPersonService:
    @staticmethod
    def create(**kwargs):
        product_person = ProductPerson(**kwargs)
        product_person.save()

        return product_person

    @staticmethod
    def is_organisation_provided(product_person: ProductPerson) -> Exception | None:
        if (
            product_person.role
            in [ProductPerson.PRODUCT_ADMIN, ProductPerson.PRODUCT_MANAGER]
            and not product_person.organisation
        ):
            raise ValidationError(
                "Organisation field must be filled for Product Admins and Managers."
            )


class ProductOwnerService:
    @staticmethod
    def create(**kwargs):
        product_owner = ProductOwner(**kwargs)
        product_owner.save()

        return product_owner
