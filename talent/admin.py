from django.contrib import admin

from .models import Person, Status, Feedback, BountyClaim

admin.site.register([Person, Status, Feedback, BountyClaim])
