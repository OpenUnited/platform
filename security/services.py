from django.contrib.auth.hashers import make_password

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


class ProductRoleAssignmentService:
    @staticmethod
    def create(**kwargs):
        product_role_assignment = ProductRoleAssignment(**kwargs)
        product_role_assignment.save()

        return product_role_assignment
