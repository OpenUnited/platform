from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from random import randrange

from .models import SignUpRequest, ProductPerson, ProductOwner, User


class UserService:
    @staticmethod
    def create(**kwargs):
        user = User(**kwargs)
        user.save()

        return user


class SignUpRequestService:
    @staticmethod
    def create(**kwargs):
        sign_up_request = SignUpRequest(**kwargs)
        sign_up_request.save()

        return sign_up_request

    @staticmethod
    def create_from_steps_form(form_list, object_id=None):
        """
        Create a SignUpRequest object from a list of multi-step form data.

        This method takes a list of Django forms collected from a multi-step form and creates a SignUpRequest object.
        The form_list should contain the data from each step of the form in order (e.g., Step 1 form, Step 2 form, ...).

        Parameters:
            form_list (list): A list of Django forms containing the data from each step of the multi-step form.
            object_id (int or None): An optional parameter. If provided, the method will update an existing SignUpRequest
                                    object with the given ID. If not provided, a new SignUpRequest object will be created.

        Example:
            # Assuming `Step1Form`, `Step2Form`, and `Step3Form` are the form classes used in the multi-step form.

            # Create a list of form instances with data from each step
            form_list = [
                Step1Form(data={'full_name': 'John Doe', 'email': 'john@example.com'}),
                Step2Form(data={'some_field': 'some_value'}),
                Step3Form(data={'username': 'johndoe123', 'password': 'securepassword'}),
            ]

            # Create a new SignUpRequest object
            create_from_steps_form(form_list)

            # Update an existing SignUpRequest object with ID=1
            create_from_steps_form(form_list, object_id=1)

        Note:
            - The provided `form_list` should be in the order of form steps, i.e., the first element of the list should
            contain the data from the first step, the second element from the second step, and so on.
            - This method assumes that `SignUpRequest` is a model representing sign-up requests and has the fields:
            `full_name`, `email`, `username`, and `password`.
            - The password is hashed using Django's `make_password` function before saving it to the database.

        """

        if object_id:
            sign_up_request = SignUpRequest.objects.get(id=object_id)
        else:
            sign_up_request = SignUpRequest()

        first_form_data = form_list[0].cleaned_data
        third_form_data = form_list[2].cleaned_data

        full_name = first_form_data.get("full_name")
        email = first_form_data.get("email")
        username = third_form_data.get("username")
        password = third_form_data.get("password")

        sign_up_request.full_name = full_name
        sign_up_request.email = email

        sign_up_request.username = username
        sign_up_request.password = make_password(password)

        # note: we are ignoring the middle name, if any
        first_name = full_name.split(" ")[0]
        last_name = full_name.split(" ")[-1]
        user = UserService.create(
            first_name=first_name.title(),
            last_name=last_name.title(),
            username=username,
            email=email,
            password=password,
        )

        sign_up_request.user = user
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
