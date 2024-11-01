from __future__ import absolute_import  # Python 2 only

from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from django.templatetags.static import static
from django.middleware.csrf import get_token
from django.utils.safestring import mark_safe
from jinja2 import Environment

from apps.talent.templatetags.custom_filters import expertise_filter, get_ids


def environment(**options):
    env = Environment(**options)
    env.filters["get_ids"] = get_ids
    env.filters["expertise_filter"] = expertise_filter

    def get_csrf_token(request):
        return get_token(request)

    env.globals.update(
        {
            "static": staticfiles_storage.url,
            "url": reverse,
            "get_csrf_token": get_csrf_token,
        }
    )

    return env
