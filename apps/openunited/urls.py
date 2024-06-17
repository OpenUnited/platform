from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

from apps.canopy.views import ProductTreeUpdateView, ProductTreeView

from . import views

handler404 = views.custom_404_view

urlpatterns = []

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]

if settings.ADMIN_CONTEXT:
    urlpatterns += [
        path(f"{settings.ADMIN_CONTEXT}/admin/", admin.site.urls),
    ]
else:
    urlpatterns += [
        path("admin/", admin.site.urls),
    ]

urlpatterns += [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("privacy-policy/", views.privacy_policy, name="privacy-policy"),
    path("terms-of-use/", views.terms_of_use, name="terms-of-use"),
    path("enterprise-customers/", views.enterprise_customers, name="enterprise-customers"),
    path("canopy/", include("apps.canopy.urls")),
    path("canopy", RedirectView.as_view(url="/canopy/")),
    path("version/", views.version_view, name="version"),
    path("talent/", include("apps.talent.urls")),
    path("freshlatte", RedirectView.as_view(url="/canopy/")),
    path("", include("apps.security.urls")),
    path("", include("apps.product_management.urls")),
    path("", include("social_django.urls", namespace="social")),
    path("tinymce/", include("tinymce.urls")),
    path("product-tree", ProductTreeView.as_view()),
    path("product-tree/", ProductTreeView.as_view(), name="shareable_product_tree"),
    path("product-tree/share/<str:pk>", ProductTreeUpdateView.as_view(), name="update_product_tree"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
