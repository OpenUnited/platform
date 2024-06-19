from django.urls import path

from . import views

app_name = "canopy"
urlpatterns = [
    path("", views.introduction, name="introduction"),
    path("chapter-1/", views.chapter1, name="chapter1"),
    path("reset-tree/", views.reset_tree, name="reset_tree"),
    path("update-node/<int:pk>", views.update_node, name="update_node"),
    path("add-node/<str:tree_id>/root", views.add_root_node, name="add_node_root"),
    path("add-node/<int:parent_id>/child", views.add_node, name="add_node"),
    path("delete-node/<int:pk>", views.delete_node, name="delete_node"),
]
