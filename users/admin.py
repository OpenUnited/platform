from django.contrib import admin

from users.models import User, BlacklistedUsernames


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active', 'is_staff', 'is_superuser')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email')
    ordering = ('username',)


admin.site.register(User, UserAdmin)
admin.site.register(BlacklistedUsernames)
