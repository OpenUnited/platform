import logging
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError

from .models import SignUpRequest, ProductPerson, ProductOwner

logger = logging.getLogger(__name__)


class SignUpRequestService:
    @staticmethod
    def create(**kwargs):
        sign_up_request = SignUpRequest(**kwargs)
        sign_up_request.save()

        return sign_up_request

    @staticmethod
    def create_from_steps_form(form_list):
        sign_up_request = SignUpRequest()

        first_form_data = form_list[0].cleaned_data

        sign_up_request.full_name = first_form_data.get("full_name")
        sign_up_request.email = first_form_data.get("email")

        second_form_data = form_list[1].cleaned_data

        sign_up_request.verification_code = second_form_data.get("verification_code")

        third_form_data = form_list[2].cleaned_data

        sign_up_request.username = third_form_data.get("username")
        sign_up_request.password = make_password(third_form_data.get("password"))

        sign_up_request.save()


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
