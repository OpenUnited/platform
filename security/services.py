from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from random import randrange

from talent.models import Person
from .models import SignUpRequest, ProductRoleAssignment, User


class UserService:
    @staticmethod
    def create(**kwargs):
        password = kwargs.pop("password")
        user = User(**kwargs)
        if password:
            user.password = make_password(password)
        user.save()

        return user


class SignUpRequestService:
    @staticmethod
    def create(**kwargs):
        sign_up_request = SignUpRequest(**kwargs)
        sign_up_request.save()

        return sign_up_request

    # TODO: Write a docstring when this method is complete
    @staticmethod
    def create_from_steps_form(form_list, object_id=None):
        if object_id:
            sign_up_request = SignUpRequest.objects.get(id=object_id)
        else:
            sign_up_request = SignUpRequest()

        first_form_data = form_list[0].cleaned_data
        second_form_data = form_list[1].cleaned_data
        third_form_data = form_list[2].cleaned_data

        full_name = first_form_data.get("full_name")
        preferred_name = first_form_data.get("preferred_name")
        email = first_form_data.get("email")
        verification_code = second_form_data.get("verification_code")
        username = third_form_data.get("username")
        password = third_form_data.get("password")

        # TODO: assign device_hash, country, region code etc. when the js libraries are set up
        sign_up_request.verification_code = verification_code

        user = UserService.create(
            username=username,
            password=password,
            email=email,
        )

        _ = Person.objects.create(
            full_name=full_name,
            preferred_name=preferred_name,
            user=user,
        )

        sign_up_request.user = user
        sign_up_request.save()


class ProductRoleAssignmentService:
    @staticmethod
    def create(**kwargs):
        product_role_assignment = ProductRoleAssignment(**kwargs)
        product_role_assignment.save()

        return product_role_assignment


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
