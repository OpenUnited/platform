import re
from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """
    Manager for a custom User model
    """

    def create_user(self, username, email, password=None):
        from .models import BlacklistedUsernames, Organisation

        if not username:
            raise ValueError("Username should be provided!")
        elif BlacklistedUsernames.objects.filter(username=username).exists():
            raise ValueError("Username is not valid!")
        elif Organisation.objects.filter(username=username).exists():
            raise ValueError("You can't have the same username as organisation name!")
        elif not re.match(r'^[a-z0-9]*$', username):
            raise ValueError("Username may only contain letters and numbers")
        user = self.model(username=username, email=email)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None):
        user = self.create_user(username, email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        return user
