from django.contrib import admin

from .models import Person


class PersonAdmin(admin.ModelAdmin):
    exclude = ("id",)


admin.site.register(Person, PersonAdmin)
