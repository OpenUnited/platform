from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class EmailOrUsernameModelBackend(ModelBackend):
    """
    This is a ModelBacked that allows authentication
    with either a username or an email address.
    """

    def authenticate(self, request, username, password, **kwargs):
        UserModel = get_user_model()

        user = UserModel.objects.get_user_by_username_or_email(username)

        if user and user.check_password(password):
            return user
