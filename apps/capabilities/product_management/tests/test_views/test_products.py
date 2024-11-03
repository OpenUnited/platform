from django.http import HttpResponseRedirect
from django.urls import reverse

from apps.capabilities.product_management.models import Product


def test_product_list_view_pagination(client, auth_user, products):
    url = reverse("products")
    res_1 = client.get(url)
    assert res_1.status_code == 200
    assert "products" in res_1.context_data
    assert len(res_1.context_data["products"]) == 8

    res_2 = client.get(f"{url}?page=2")
    assert "products" in res_2.context_data
    assert len(res_2.context_data["products"]) == 2


def test_product_detail(client, product):
    url = reverse("product_detail", args=(product.slug,))
    res = client.get(url)
    assert res.status_code == 302
    assert isinstance(res, HttpResponseRedirect)


def test_product_summary(client, auth_user, product_areas, product_role_assignment_admin):
    url = reverse("product_summary", args=(product_role_assignment_admin.product.slug,))
    res = client.get(url)
    assert res.status_code == 200
    context = res.context_data
    assert context["can_modify_product"] == True
    assert "challenges" in context
    assert isinstance(context["tree_data"], list)


def test_post_product_creation(client, auth_user, product_data, organisation):
    res = client.post(reverse("create-product"), product_data)
    product = Product.objects.first()
    assert product.name == product_data["name"]
    assert product.full_description == product_data["full_description"]
    assert res.status_code == 302


def test_post_product_update(client, auth_user, product_data, product, organisation):
    res = client.post(reverse("update-product", args=(product.pk,)), product_data)
    product = Product.objects.filter(pk=product.pk).first()
    assert product.name == product_data["name"]
    assert product.full_description == product_data["full_description"]
    assert res.status_code == 302
