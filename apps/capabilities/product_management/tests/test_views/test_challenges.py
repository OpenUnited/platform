from django.urls import reverse

from apps.capabilities.product_management.models import Challenge, Product


def test_dashboard_product_challenges(client, auth_user, challenges):
    product = challenges[0].product
    url = reverse("dashboard-product-challenges", args=(product.slug,))
    res = client.get(url)
    assert res.status_code == 200
    context = res.context_data
    assert "challenges" in context
    assert len(context["challenges"]) == 10


def test_challenge_detail_view(client, auth_user, challenge):
    url = reverse(
        "challenge_detail",
        args=(challenge.product.slug, challenge.pk),
    )
    res = client.get(url)
    assert res.status_code == 200
    html_content = res.content.decode("utf-8")
    assert "<title>Challenge Detail</title>" in html_content


def test_challenge_create(client, auth_user, challenge_data):
    product = Product.objects.get(pk=challenge_data["product"])
    url = reverse("create-challenge", args=(product.slug,))
    res = client.post(url, challenge_data)
    assert res.status_code == 302
    challenge = Challenge.objects.first()
    assert challenge.title == challenge_data["title"]
    assert challenge.description == challenge_data["description"]
    assert challenge.status == challenge_data["status"]


def test_challenge_update(client, auth_user, challenge, challenge_update_data):
    challenge_update_data["product"] = challenge.product.pk
    url = reverse("update-challenge", args=(challenge.product.slug, challenge.pk))
    res = client.post(url, challenge_update_data)
    challenge = Challenge.objects.filter(pk=challenge.pk).first()
    assert res.status_code == 302
    assert challenge.title == challenge_update_data["title"]
    assert challenge.description == challenge_update_data["description"]
    assert challenge.status == challenge_update_data["status"]
