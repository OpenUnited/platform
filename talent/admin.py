from django.contrib import admin

from .models import Person, Status, Feedback

admin.site.register([Person, Status, Feedback])
