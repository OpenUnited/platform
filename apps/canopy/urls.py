from django.urls import path

from . import views

app_name = "canopy"
urlpatterns = [
    path("", views.introduction, name="introduction"),
    path("chapter-1/", views.chapter1, name="chapter1"),
    path("update-node/<int:pk>", views.update_node, name="update_node"),
    path("add-node/<int:parent_id>", views.add_node, name="add_node"),
    path("delete-node/<int:pk>", views.delete_node, name="delete_node"),
]
