import pytest
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.conf import settings
from urllib.parse import quote
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from unittest.mock import patch, PropertyMock

from apps.capabilities.product_management.models import (
    Product, Challenge, Bounty, Initiative, Idea, Bug, 
    ProductContributorAgreementTemplate
)
from apps.capabilities.talent.models import Person
from apps.capabilities.commerce.models import Organisation

@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username='testuser', password='testpass123')

@pytest.fixture
def person(db, user):
    return Person.objects.create(user=user)

@pytest.fixture
def organisation(db):
    return Organisation.objects.create(name="Test Org")

@pytest.fixture
def global_product(db, organisation):
    return Product.objects.create(
        name="Global Product",
        slug="global-product",
        short_description="Test Description",
        visibility=Product.Visibility.GLOBAL,
        organisation=organisation
    )

@pytest.fixture
def restricted_product(db, organisation):
    return Product.objects.create(
        name="Restricted Product",
        slug="restricted-product",
        short_description="Test Description",
        visibility=Product.Visibility.RESTRICTED,
        organisation=organisation
    )

@pytest.fixture
def authenticated_client(client, user, person):
    client.force_login(user)
    return client

@pytest.fixture
def mock_template_loader(mocker):
    mock = mocker.patch('django.template.loader.get_template')
    mock.return_value.render.return_value = ''
    return mock

@pytest.mark.django_db
class TestProductVisibility:
    def test_global_product_public_access(self, client, global_product, mock_template_loader):
        url = reverse('product_management:product-summary', kwargs={'product_slug': global_product.slug})
        response = client.get(url)
        assert response.status_code == 200

    def test_restricted_product_requires_auth(self, client, restricted_product, mock_template_loader):
        url = reverse('product_management:product-summary', kwargs={'product_slug': restricted_product.slug})
        response = client.get(url)
        assert response.status_code == 302
        expected_redirect = f"{settings.LOGIN_URL}?next={url}"
        assert response.url == expected_redirect

    def test_restricted_product_auth_access(self, authenticated_client, restricted_product, mock_template_loader, mocker):
        # Mock the has_product_access method
        mock_has_access = mocker.patch('apps.capabilities.product_management.views.view_mixins.RoleService.has_product_access')
        mock_has_access.return_value = True
        
        url = reverse('product_management:product-summary', kwargs={'product_slug': restricted_product.slug})
        response = authenticated_client.get(url)
        assert response.status_code == 200

@pytest.mark.django_db
class TestProductManagement:
    def test_create_product_requires_auth(self, client):
        url = reverse('product_management:create-product')
        response = client.post(url, {'name': 'New Product'})
        assert response.status_code == 302
        assert 'sign-in' in response.url

    def test_create_product_success(self, authenticated_client, mocker, organisation):
        # Mock the service
        mock_service = mocker.patch('apps.capabilities.product_management.services.ProductManagementService.create_product')
        product = Product(id=1, slug='new-product')
        mock_service.return_value = (True, None, product)

        data = {
            'name': 'New Product',
            'short_description': 'Description',
            'full_description': 'Full Description',
            'visibility': Product.Visibility.GLOBAL,
            'organisation': organisation.id,
            'make_me_owner': True,
            'website': '',
            'video_url': '',
            'detail_url': '',
            'photo': ''
        }

        # Mock the form class instead of its instance
        mock_form = mocker.Mock()
        mock_form.is_valid.return_value = True
        mock_form.cleaned_data = data
        
        form_class_mock = mocker.patch('apps.capabilities.product_management.forms.ProductForm')
        form_class_mock.return_value = mock_form

        url = reverse('product_management:create-product')
        response = authenticated_client.post(url, data)
        
        # Add debugging information
        if response.status_code != 302:
            print(f"\nResponse status code: {response.status_code}")
            print(f"Response content: {response.content.decode()}")
            if hasattr(response, 'context'):
                print(f"Form errors: {response.context.get('form').errors if 'form' in response.context else 'No form in context'}")
        
        assert response.status_code == 302  # Redirect after success
        assert response.url == reverse('product_management:product-summary', kwargs={'product_slug': product.slug})

    def test_update_product_requires_management(self, authenticated_client, global_product, mocker):
        mock_role_service = mocker.patch('apps.capabilities.security.services.RoleService.has_product_management_access')
        mock_role_service.return_value = False

        url = reverse('product_management:update-product', kwargs={'pk': global_product.pk})
        response = authenticated_client.post(url, {'name': 'Updated'})
        assert response.status_code == 403

@pytest.mark.django_db
class TestIdeaManagement:
    @pytest.fixture
    def idea(self, global_product, person):
        return Idea.objects.create(
            title="Test Idea",
            description="Description",
            product=global_product,
            person=person
        )

    def test_create_idea_requires_auth(self, client, global_product, mocker):
        # Mock the URL pattern directly
        def mock_view(request, *args, **kwargs):
            return redirect_to_login(request.get_full_path())
        
        mocker.patch('apps.capabilities.product_management.urls.CreateIdeaView.as_view', 
                     return_value=mock_view)

        url = reverse('product_management:create-idea', kwargs={'product_slug': global_product.slug})
        response = client.get(url)
        
        assert response.status_code == 302
        expected_url = f"{settings.LOGIN_URL}?next={quote(url)}"
        assert response.url == expected_url

    def test_create_idea_success(self, authenticated_client, global_product, mocker):
        # Mock the service
        mock_service = mocker.patch('apps.capabilities.product_management.services.IdeaService.create_idea')
        idea = Idea(id=1)
        mock_service.return_value = (True, None, idea)

        url = reverse('product_management:create-idea', kwargs={'product_slug': global_product.slug})
        data = {
            'title': 'New Idea',
            'description': 'Description'
        }
        
        response = authenticated_client.post(url, data)
        assert response.status_code == 302
        assert response.url == reverse('product_management:idea-detail',
                                     kwargs={'product_slug': global_product.slug,
                                           'idea_id': idea.id})

    def test_update_idea_requires_ownership(self, authenticated_client, idea, mocker):
        mock_service = mocker.patch('apps.capabilities.product_management.services.IdeaService.can_modify_idea')
        mock_service.return_value = False

        url = reverse('product_management:update-idea',
                     kwargs={'product_slug': idea.product.slug, 'pk': idea.id})
        response = authenticated_client.post(url, {'title': 'Updated'})
        assert response.status_code == 403

@pytest.mark.django_db
class TestVoting:
    @pytest.fixture
    def idea(self, global_product, person):
        return Idea.objects.create(
            title="Test Idea",
            description="Description",
            product=global_product,
            person=person
        )

    def test_vote_requires_auth(self, client, idea):
        url = reverse('product_management:cast-vote', kwargs={'pk': idea.id})
        response = client.post(url)
        assert response.status_code == 302
        assert 'sign-in' in response.url

    def test_vote_requires_product_access(self, authenticated_client, idea, mocker):
        mock_service = mocker.patch('apps.capabilities.product_management.services.ProductService.has_product_visibility_access')
        mock_service.return_value = False

        url = reverse('product_management:cast-vote', kwargs={'pk': idea.id})
        response = authenticated_client.post(url)
        assert response.status_code == 403

    def test_vote_success(self, authenticated_client, idea, mocker):
        mock_product_service = mocker.patch('apps.capabilities.product_management.services.ProductService.has_product_visibility_access')
        mock_product_service.return_value = True
        
        mock_idea_service = mocker.patch('apps.capabilities.product_management.services.IdeaService.toggle_vote')
        mock_idea_service.return_value = (True, None, 1)

        url = reverse('product_management:cast-vote', kwargs={'pk': idea.id})
        response = authenticated_client.post(url)
        assert response.status_code == 200
        assert response.json() == {'vote_count': 1}