import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

from apps.capabilities.product_management.models import (
    Product, Challenge, Bounty, Initiative, Idea, Bug
)
from apps.capabilities.commerce.models import Organisation 
from apps.capabilities.security.models import Person

User = get_user_model()

@pytest.fixture
def organisation():
    return Organisation.objects.create(name="Test Org")

@pytest.fixture
def product(organisation):
    return Product.objects.create(
        slug='test-product',
        name='Test Product',
        visibility=Product.Visibility.GLOBAL,
        organisation=organisation
    )

@pytest.fixture
def restricted_product(organisation):
    return Product.objects.create(
        slug='private-product',
        name='Private Product',
        visibility=Product.Visibility.RESTRICTED,
        organisation=organisation
    )

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def user(db):
    return User.objects.create_user(username='testuser', password='12345')

@pytest.fixture
def authenticated_client(client):
    user = User.objects.create_user(username='testuser', password='12345')
    # Create associated Person object
    person = Person.objects.create(
        user=user,
        points=0,
        full_name="Test Person",
        preferred_name="Test",
        headline="Test Headline",
        overview="Test Overview",
        send_me_bounties=False
    )
    client.login(username='testuser', password='12345')
    client.user = user  # Store the user object on the client
    return client

@pytest.mark.django_db
class TestPublicBountyListView:
    def test_bounty_list_uses_bounty_service(self, authenticated_client, mocker):
        # Mock both services that BountyService depends on
        visible_products = [
            Product(id=1, name='Product 1'),
            Product(id=2, name='Product 2')
        ]
        mock_product_service = mocker.patch(
            'apps.capabilities.product_management.services.ProductService.get_visible_products',
            return_value=visible_products
        )

        mock_bounties = Bounty.objects.none()
        mock_bounty_service = mocker.patch(
            'apps.capabilities.product_management.services.BountyService.get_visible_bounties',
            return_value=mock_bounties
        )

        response = authenticated_client.get(reverse('product_management:bounty-list'))
        
        mock_bounty_service.assert_called_once_with(authenticated_client.user)
        assert list(response.context['bounties']) == list(mock_bounties)

@pytest.mark.django_db
class TestProductVisibilityMixin:
    def test_anonymous_user_can_access_global_product(self, client, product, mocker):
        product.save()
        response = client.get(
            reverse('product_management:product-summary',
            kwargs={'product_slug': product.slug})
        )
        assert response.status_code == 200

    def test_anonymous_user_cannot_access_restricted_product(self, client, mocker, restricted_product):
        restricted_product.save()
        response = client.get(
            reverse('product_management:product-summary',
            kwargs={'product_slug': restricted_product.slug})
        )
        assert response.status_code == 302

@pytest.mark.django_db
class TestProductChallengesView:
    def test_challenge_service_integration(self, authenticated_client, product, mocker):
        # Mock ChallengeService as implemented in services.py
        mock_challenges = Challenge.objects.none()
        mock_challenge_service = mocker.patch(
            'apps.capabilities.product_management.services.ChallengeService.get_product_challenges',
            return_value=mock_challenges
        )

        # Mock RoleService for permission check
        mock_role_service = mocker.patch(
            'apps.capabilities.security.services.RoleService.has_product_management_access',
            return_value=True
        )

        product.save()
        response = authenticated_client.get(
            reverse('product_management:product-challenges', 
            kwargs={'product_slug': product.slug})
        )

        # Verify service interactions match implementation
        mock_challenge_service.assert_called_once_with(product)
        assert response.context['challenges'] == mock_challenges

@pytest.mark.django_db
class TestProductIdeasAndBugsView:
    def test_ideas_and_bugs_service_integration(self, authenticated_client, product, mocker):
        # Mock the services
        mock_ideas = Idea.objects.none()
        mock_bugs = Bug.objects.none()
        
        mocker.patch(
            'apps.capabilities.product_management.services.IdeaService.get_product_ideas',
            return_value=mock_ideas
        )
        mocker.patch(
            'apps.capabilities.product_management.services.BugService.get_product_bugs',
            return_value=mock_bugs
        )

        product.save()
        response = authenticated_client.get(
            reverse('product_management:product-ideas-bugs', 
            kwargs={'product_slug': product.slug})
        )

        assert response.status_code == 200
        assert response.context['ideas'] == mock_ideas
        assert response.context['bugs'] == mock_bugs

@pytest.mark.django_db
class TestProductListView:
    def test_anonymous_user_sees_only_global_products(self, client, product, mocker):
        product.save()
        restricted_product = Product.objects.create(
            slug='restricted-product',
            name='Restricted Product',
            visibility=Product.Visibility.RESTRICTED
        )
        
        response = client.get(reverse('product_management:products'))
        assert response.status_code == 200
        assert product in response.context['products']
        assert restricted_product not in response.context['products']

    def test_authenticated_user_sees_create_button(self, authenticated_client, product, mocker):
        response = authenticated_client.get(reverse('product_management:products'))
        assert response.status_code == 200
        assert b'Create Product' in response.content

@pytest.mark.django_db
class TestProductInitiativesView:
    def test_initiative_service_integration(self, authenticated_client, product, mocker):
        # Create the initiative first
        initiative = Initiative.objects.create(
            product=product,
            name='Test Initiative',
            description='Test'
        )
        
        # Mock InitiativeService to return our initiative
        mock_initiatives = Initiative.objects.filter(id=initiative.id)
        mock_service = mocker.patch(
            'apps.capabilities.product_management.services.InitiativeService.get_product_initiatives',
            return_value=mock_initiatives
        )

        # Mock user having management access
        mocker.patch(
            'apps.capabilities.security.services.RoleService.has_product_management_access',
            return_value=True
        )

        product.save()
        response = authenticated_client.get(
            reverse('product_management:product-initiatives', 
            kwargs={'product_slug': product.slug})
        )

        # Verify service interactions
        mock_service.assert_called_once_with(product)
        assert response.status_code == 200
        assert response.context['can_manage'] == True
        assert initiative in response.context['initiatives']

@pytest.mark.django_db
class TestProductSummaryView:
    def test_summary_view_uses_services(self, authenticated_client, product, mocker):
        # Mock services
        mock_challenges = Challenge.objects.none()
        mocker.patch(
            'apps.capabilities.product_management.models.Challenge.objects.filter',
            return_value=mock_challenges
        )

        product.save()
        response = authenticated_client.get(
            reverse('product_management:product-summary', 
            kwargs={'product_slug': product.slug})
        )

        assert response.status_code == 200
        assert response.context['challenges'] == mock_challenges
        assert response.context['product'] == product

@pytest.mark.django_db
class TestProductTreeInteractiveView:
    def test_tree_view_uses_services(self, authenticated_client, product, mocker):
        mock_tree_data = [{'id': 1, 'name': 'Area 1'}]
        mock_tree_service = mocker.patch(
            'apps.capabilities.product_management.services.ProductTreeService.get_product_tree_data',
            return_value=mock_tree_data
        )
        mock_role_service = mocker.patch(
            'apps.capabilities.security.services.RoleService.has_product_management_access',
            return_value=True
        )

        product.save()
        response = authenticated_client.get(
            reverse('product_management:product-tree', 
            kwargs={'product_slug': product.slug})
        )

        mock_tree_service.assert_called_once_with(product)
        assert response.context['tree_data'] == mock_tree_data
        assert response.context['can_manage'] == True

@pytest.mark.django_db
class TestProductPeopleView:
    def test_people_view_uses_services(self, authenticated_client, product, mocker):
        mock_roles = [(1, []), (2, [])]
        mock_people_service = mocker.patch(
            'apps.capabilities.product_management.services.ProductPeopleService.get_grouped_product_roles',
            return_value=mock_roles
        )

        product.save()
        response = authenticated_client.get(
            reverse('product_management:product-people',
            kwargs={'product_slug': product.slug})
        )

        mock_people_service.assert_called_with(product)
        assert response.context['grouped_product_people'] == mock_roles

@pytest.mark.django_db
class TestProductListView:
    def test_list_view_uses_product_service(self, authenticated_client, mocker):
        mock_products = Product.objects.none()
        mock_product_service = mocker.patch(
            'apps.capabilities.product_management.services.ProductService.get_visible_products',
            return_value=mock_products
        )

        response = authenticated_client.get(reverse('product_management:products'))
        
        mock_product_service.assert_called_once_with(authenticated_client.user)
        assert list(response.context['products']) == list(mock_products)

@pytest.mark.django_db
class TestProductIdeasAndBugsView:
    def test_ideas_and_bugs_view_uses_services(self, authenticated_client, product, mocker):
        mock_ideas = Idea.objects.none()
        mock_bugs = Bug.objects.none()
        
        mocker.patch(
            'apps.capabilities.product_management.models.Idea.objects.filter',
            return_value=mock_ideas
        )
        mocker.patch(
            'apps.capabilities.product_management.models.Bug.objects.filter',
            return_value=mock_bugs
        )

        product.save()
        response = authenticated_client.get(
            reverse('product_management:product-ideas-bugs', 
            kwargs={'product_slug': product.slug})
        )

        assert response.context['ideas'] == mock_ideas
        assert response.context['bugs'] == mock_bugs
        assert response.context['product'] == product

@pytest.mark.django_db
class TestBountyDetailView:
    def test_bounty_detail_uses_role_service(self, authenticated_client, product, mocker):
        # Add mock at the start of the test
        mock_role_service = mocker.patch(
            'apps.capabilities.security.services.RoleService.has_product_management_access',
            return_value=True
        )
        
        challenge = Challenge.objects.create(product=product, title='Test Challenge')
        bounty = Bounty.objects.create(
            challenge=challenge,
            title='Test Bounty',
            points=10  # Required field
        )
        response = authenticated_client.get(
            reverse('product_management:bounty-detail',
            kwargs={
                'product_slug': product.slug,
                'challenge_id': challenge.id,
                'pk': bounty.id
            })
        )
        mock_role_service.assert_called_once_with(
            authenticated_client.user.person,
            product
        )
        assert response.context['data']['show_actions'] == True
        assert response.context['data']['bounty'] == bounty