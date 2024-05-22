from django.urls import reverse
from product_management.models import Initiative, Product


def test_product_initiatives(client, auth_user, product_initiatives):
    product = product_initiatives[0].product
    url = reverse("product_initiatives", args=(product.slug,))
    res = client.get(url)
    assert res.status_code == 200
    context = res.context_data
    assert "initiatives" in context
    assert len(context["initiatives"]) == 10


def test_create_initiative_view(client, auth_user, initiative_data):
    product = Product.objects.get(pk=initiative_data["product"])
    url = reverse("create-initiative", args=(product.slug,))

    res = client.post(url, data=initiative_data)
    assert Initiative.objects.first().name == initiative_data["name"]
    assert Initiative.objects.first().status == initiative_data["status"]
    assert Initiative.objects.first().status == initiative_data["status"]
    assert res.status_code == 302
