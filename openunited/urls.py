from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from openunited import settings
from . import views

handler404 = views.custom_404_view

urlpatterns = []

if settings.development.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]

urlpatterns += [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("talent/", include("talent.urls")),
    path("", include("security.urls")),
    path("", include("product_management.urls")),
]

urlpatterns += static(settings.base.MEDIA_URL, document_root=settings.base.MEDIA_ROOT)
