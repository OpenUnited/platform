from django.contrib.auth.hashers import make_password

from .models import User


class UserService:
    @staticmethod
    def create(**kwargs):
        password = kwargs.pop("password")
        user = User(**kwargs)
        if password:
            user.password = make_password(password)
        user.save()

        return user
