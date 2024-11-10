import pytest
from django.urls import reverse
from django.test import Client

from apps.capabilities.product_management.models import (
    Product, Challenge, Bounty, Initiative, Idea, Bug
)

@pytest.fixture
def product():
    return Product(
        id=1,
        slug='test-product',
        name='Test Product',
        visibility=Product.Visibility.GLOBAL
    )

@pytest.fixture
def restricted_product():
    return Product(
        id=2,
        slug='private-product',
        name='Private Product',
        visibility=Product.Visibility.RESTRICTED
    )

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def user(db):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(username='testuser', password='12345')

@pytest.fixture
def authenticated_client(client, user):
    client.force_login(user)
    return client

@pytest.mark.django_db
class TestPublicBountyListView:
    def test_anonymous_user_sees_only_global_bounties(self, client, mocker):
        global_product = Product.objects.create(
            slug='global-product',
            name='Global Product',
            visibility=Product.Visibility.GLOBAL
        )
        restricted_product = Product.objects.create(
            slug='restricted-product',
            name='Restricted Product',
            visibility=Product.Visibility.RESTRICTED
        )
        
        global_bounty = Bounty.objects.create(
            product=global_product,
            title='Global Bounty',
            description='Test'
        )
        restricted_bounty = Bounty.objects.create(
            product=restricted_product,
            title='Restricted Bounty',
            description='Test'
        )

        response = client.get(reverse('product_management:bounty-list'))
        assert response.status_code == 200
        assert len(response.context['bounties']) == 1
        assert global_bounty in response.context['bounties']
        assert restricted_bounty not in response.context['bounties']

    def test_authenticated_user_sees_accessible_bounties(self, authenticated_client, mocker):
        global_product = Product.objects.create(
            slug='global-product',
            name='Global Product',
            visibility=Product.Visibility.GLOBAL
        )
        restricted_product = Product.objects.create(
            slug='restricted-product',
            name='Restricted Product',
            visibility=Product.Visibility.RESTRICTED
        )
        
        # Mock user access to restricted product
        mocker.patch('apps.capabilities.product_management.models.Product.user_has_access', return_value=True)
        
        global_bounty = Bounty.objects.create(
            product=global_product,
            title='Global Bounty',
            description='Test'
        )
        restricted_bounty = Bounty.objects.create(
            product=restricted_product,
            title='Restricted Bounty',
            description='Test'
        )

        response = authenticated_client.get(reverse('product_management:bounty-list'))
        assert response.status_code == 200
        assert len(response.context['bounties']) == 2
        assert global_bounty in response.context['bounties']
        assert restricted_bounty in response.context['bounties']

@pytest.mark.django_db
class TestProductVisibilityMixin:
    def test_anonymous_user_can_access_global_product(self, client, product, mocker):
        product.save()
        response = client.get(reverse('product_management:product-detail', kwargs={'slug': product.slug}))
        assert response.status_code == 200
        assert response.context['product'] == product

    def test_anonymous_user_cannot_access_restricted_product(self, client, mocker, restricted_product):
        restricted_product.save()
        response = client.get(reverse('product_management:product-detail', kwargs={'slug': restricted_product.slug}))
        assert response.status_code == 403

@pytest.mark.django_db
class TestProductChallengesView:
    def test_authenticated_user_with_access_sees_management_controls(self, authenticated_client, product, mocker):
        product.save()
        challenge = Challenge.objects.create(
            product=product,
            title='Test Challenge',
            description='Test'
        )
        
        # Mock user having management access
        mocker.patch('apps.capabilities.product_management.models.Product.user_has_management_access', return_value=True)
        
        response = authenticated_client.get(reverse('product_management:product-challenges', kwargs={'slug': product.slug}))
        assert response.status_code == 200
        assert response.context['can_manage'] == True
        assert challenge in response.context['challenges']

@pytest.mark.django_db
class TestProductIdeasAndBugsView:
    def test_ideas_and_bugs_visible_for_global_product(self, client, product, mocker):
        product.save()
        idea = Idea.objects.create(
            product=product,
            title='Test Idea',
            description='Test'
        )
        bug = Bug.objects.create(
            product=product,
            title='Test Bug',
            description='Test'
        )
        
        response = client.get(reverse('product_management:product-ideas-bugs', kwargs={'slug': product.slug}))
        assert response.status_code == 200
        assert idea in response.context['ideas']
        assert bug in response.context['bugs']

@pytest.mark.django_db
class TestProductListView:
    def test_anonymous_user_sees_only_global_products(self, client, product, mocker):
        product.save()
        restricted_product = Product.objects.create(
            slug='restricted-product',
            name='Restricted Product',
            visibility=Product.Visibility.RESTRICTED
        )
        
        response = client.get(reverse('product_management:product-list'))
        assert response.status_code == 200
        assert product in response.context['products']
        assert restricted_product not in response.context['products']

    def test_authenticated_user_sees_create_button(self, authenticated_client, product, mocker):
        response = authenticated_client.get(reverse('product_management:product-list'))
        assert response.status_code == 200
        assert b'Create Product' in response.content

@pytest.mark.django_db
class TestProductInitiativesView:
    def test_initiative_visibility_and_management_access(self, authenticated_client, product, mocker):
        product.save()
        initiative = Initiative.objects.create(
            product=product,
            title='Test Initiative',
            description='Test'
        )
        
        # Mock user having management access
        mocker.patch('apps.capabilities.product_management.models.Product.user_has_management_access', return_value=True)
        
        response = authenticated_client.get(reverse('product_management:product-initiatives', kwargs={'slug': product.slug}))
        assert response.status_code == 200
        assert response.context['can_manage'] == True
        assert initiative in response.context['initiatives']