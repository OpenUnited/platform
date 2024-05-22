from django.urls import reverse
from django.http import HttpResponseRedirect


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


def test_product_summary(
    client, auth_user, productAreas, product_role_assignment_admin
):
    url = reverse(
        "product_summary", args=(product_role_assignment_admin.product.slug,)
    )
    res = client.get(url)
    assert res.status_code == 200
    context = res.context_data
    assert context["can_modify_product"] == True
    assert "challenges" in context
    assert isinstance(context["tree_data"], list)


def test_dashboard_product_challenges(client, auth_user, challenges):
    product = challenges[0].product
    url = reverse("dashboard-product-challenges", args=(product.slug,))
    res = client.get(url)
    assert res.status_code == 200
    context = res.context_data
    assert "challenges" in context
    assert len(context["challenges"]) == 10


def test_product_initiatives(client, auth_user, product_initiatives):
    product = product_initiatives[0].product
    url = reverse("product_initiatives", args=(product.slug,))
    res = client.get(url)
    assert res.status_code == 200
    context = res.context_data
    assert "initiatives" in context
    assert len(context["initiatives"]) == 10


def test_bounties(client, auth_user, bounties, skills, expertise_list):
    url = reverse("bounties")
    res = client.get(url)

    assert res.status_code == 200
    context = res.context_data
    assert "skills" in context
    assert "expertises" in context
    assert len(context["object_list"]) == 51


def test_htmx_bounties(client, auth_user, bounties, skills, expertise_list):
    url = f'{reverse("bounties")}?target=skill'
    res = client.get(url, HTTP_HX_REQUEST="true")
    assert res.status_code == 200
    context = res.json()
    assert "list_html" in context
    assert "expertise_html" in context


def test_product_bounties(client, auth_user, bounties):
    product = bounties[0].challenge.product
    url = reverse("product_bounties", args=(product.slug,))
    res = client.get(url)
    assert res.status_code == 200
    context = res.context_data
    assert context["product"].pk == product.pk
    assert context["product_slug"] == product.slug
