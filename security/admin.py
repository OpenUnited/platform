from django.contrib import admin

from .models import (
    User,
    SignInAttempt,
    SignUpRequest,
    ProductRoleAssignment,
    BlacklistedUsernames,
)

admin.site.register(
    [User, SignInAttempt, SignUpRequest, ProductRoleAssignment, BlacklistedUsernames]
)
