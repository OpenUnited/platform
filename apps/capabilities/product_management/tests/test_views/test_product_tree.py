import json

from django.urls import reverse

import pytest

from apps.capabilities.product_management.models import ProductArea


def test_product_tree_get(client, product_areas, product):
    url = reverse("product_tree", kwargs={"product_slug": product.slug})
    res = client.get(url)
    html_content = res.content.decode("utf-8")
    context = res.context_data
    assert res.status_code == 200
    assert "can_modify_product" in context
    assert "tree_data" in context
    assert "Product Tree" in html_content
