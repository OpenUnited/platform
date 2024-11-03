from django.urls import reverse

from apps.capabilities.product_management.models import Bounty, Challenge


def test_bounties(client, auth_user, bounties, skills, expertise_list):
    url = reverse("bounties")
    res = client.get(url)

    assert res.status_code == 200
    context = res.context_data
    assert "skills" in context
    assert "expertises" in context


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


def test_create_bounty(client, auth_user, bounty_data):
    """TODO we need to fix bounty create view."""
    challenge = Challenge.objects.get(pk=bounty_data["challenge"])
    url = reverse(
        "create-bounty",
        args=(challenge.product.slug, challenge.pk),
    )
    # res = client.post(url, bounty_data)
    # assert res.status_code == 200
    # bounty = Bounty.objects.first()
    # assert bounty.title == bounty_data["title"]
    # assert bounty.description == bounty_data["description"]
    # assert bounty.status == bounty_data["status"]


def test_update_bounty(client, auth_user, bounty_data):
    """TODO we need to fix bounty update view."""
    challenge = Challenge.objects.get(pk=bounty_data["challenge"])
