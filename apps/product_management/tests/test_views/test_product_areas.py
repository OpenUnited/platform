import json

from django.urls import reverse

import pytest

from apps.product_management.models import ProductArea


def test_product_area_create_view_get(client, product_areas, product):
    url = reverse("product_area", kwargs={"product_slug": product.slug})
    res = client.get(url)
    html_content = res.content.decode("utf-8")
    assert res.status_code == 200
    assert '<ul ondrop="drop(event)" class="pl-0"> ' in html_content


def test_product_area_create_view_post_valid(client, product, product_area_data):
    url = reverse("product_area", kwargs={"product_slug": product.slug})
    res = client.post(url, data=product_area_data)

    assert res.status_code == 200
    product_area = ProductArea.objects.first()
    html_content = res.content.decode("utf-8")
    assert product_area_data["name"] == product_area.name
    assert product_area_data["depth"] == product_area_data["depth"]
    assert f'<li draggable="true" id="li_node_{product_area.pk}" class="ml-">' in html_content
