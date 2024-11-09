import pytest
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.contrib.auth import get_user_model

from apps.capabilities.product_management.models import (
    Product, Challenge, Bounty, Initiative, Idea, Bug, ProductContributorAgreementTemplate
)
from apps.capabilities.talent.models import Person
from django.contrib.auth.models import User

@pytest.fixture
def product(db):
    User = get_user_model()
    return Product.objects.create(
        name="Test Product",
        short_description="Test Description",
        visibility=Product.Visibility.GLOBAL,
        person=Person.objects.create(
            user=User.objects.create(username="test")
        )
    )

@pytest.fixture
def authenticated_user(db, django_user_model):
    user = django_user_model.objects.create_user(
        username='testuser',
        password='testpass123'
    )
    return user

@pytest.fixture
def authenticated_client(client, authenticated_user):
    client.force_login(authenticated_user)
    return client

@pytest.mark.django_db
class TestBaseProductView:
    def test_unauthenticated_user_redirected_to_login(self, client, product_with_person):
        response = client.get(f'/products/{product_with_person.slug}/')
        assert response.status_code == 302
        assert 'login' in response.url

    def test_authenticated_user_with_access_allowed(self, client, user, product_with_person):
        client.force_login(user)
        response = client.get(f'/products/{product_with_person.slug}/')
        assert response.status_code == 200

@pytest.mark.django_db
class TestCreateProductView:
    def test_unauthenticated_user_cannot_create_product(self, client):
        response = client.post(reverse('product_management:create-product'), {})
        assert response.status_code == 302
        assert 'sign_in' in response.url

    def test_authenticated_user_can_create_product(self, authenticated_client, mocker):
        mock_service = mocker.patch('apps.capabilities.product_management.services.ProductManagementService.create_product')
        mock_service.return_value = (True, None, Product(id=1))
        
        form_data = {
            'name': 'New Product',
            'description': 'Test description'
        }
        
        response = authenticated_client.post(
            reverse('product_management:create-product'),
            form_data
        )
        
        assert response.status_code == 302
        mock_service.assert_called_once()

    def test_create_product_service_error_handled(self, authenticated_client, mocker):
        mock_service = mocker.patch('apps.capabilities.product_management.services.ProductManagementService.create_product')
        mock_service.return_value = (False, "Error creating product", None)
        
        response = authenticated_client.post(
            reverse('product_management:create-product'),
            {'name': 'New Product'}
        )
        
        assert response.status_code == 200
        assert 'Error creating product' in str(response.content)

@pytest.mark.django_db
class TestUpdateProductView:
    def test_update_product_requires_management_access(self, authenticated_client, product, mocker):
        mocker.patch('django.shortcuts.get_object_or_404', return_value=product)
        mock_role_service = mocker.patch('apps.capabilities.security.services.RoleService.has_product_management_access')
        mock_role_service.return_value = False

        response = authenticated_client.post(
            reverse('product_management:update-product', kwargs={'pk': product.id}),
            {'name': 'Updated Name'}
        )
        
        assert response.status_code == 302
        assert 'products' in response.url

    def test_successful_product_update(self, authenticated_client, product, mocker):
        mocker.patch('django.shortcuts.get_object_or_404', return_value=product)
        mock_role_service = mocker.patch('apps.capabilities.security.services.RoleService.has_product_management_access')
        mock_role_service.return_value = True
        mock_service = mocker.patch('apps.capabilities.product_management.services.ProductManagementService.update_product')
        mock_service.return_value = (True, None)

        response = authenticated_client.post(
            reverse('product_management:update-product', kwargs={'pk': product.id}),
            {'name': 'Updated Name'}
        )
        
        assert response.status_code == 302
        mock_service.assert_called_once()

@pytest.mark.django_db
class TestCreateContributorAgreementTemplateView:
    def test_template_creation_requires_product_access(self, authenticated_client, product, mocker):
        mocker.patch('django.shortcuts.get_object_or_404', return_value=product)
        mock_role_service = mocker.patch('apps.capabilities.security.services.RoleService.has_product_management_access')
        mock_role_service.return_value = False

        response = authenticated_client.post(
            reverse('product_management:create-agreement-template', 
                   kwargs={'product_slug': product.slug}),
            {'name': 'Template'}
        )
        
        assert response.status_code == 302
        assert 'products' in response.url

    def test_successful_template_creation(self, authenticated_client, product, mocker):
        mocker.patch('django.shortcuts.get_object_or_404', return_value=product)
        mock_role_service = mocker.patch('apps.capabilities.security.services.RoleService.has_product_management_access')
        mock_role_service.return_value = True
        mock_service = mocker.patch('apps.capabilities.product_management.services.ContributorAgreementService.create_template')
        template = ProductContributorAgreementTemplate(id=1, product=product)
        mock_service.return_value = (True, None, template)

        response = authenticated_client.post(
            reverse('product_management:create-agreement-template', 
                   kwargs={'product_slug': product.slug}),
            {'name': 'Template'}
        )
        
        assert response.status_code == 302
        mock_service.assert_called_once()

@pytest.mark.django_db
class TestProductIdeaViews:
    def test_create_idea_requires_authentication(self, client, product):
        response = client.post(
            reverse('product_management:create-idea', 
                   kwargs={'product_slug': product.slug}),
            {'title': 'New Idea'}
        )
        assert response.status_code == 302
        assert '/s/sign-in/' in response.url

    def test_update_idea_requires_ownership(self, authenticated_client, product, mocker):
        idea = Idea(id=1, product=product)
        mocker.patch('django.shortcuts.get_object_or_404', return_value=idea)
        mock_service = mocker.patch('apps.capabilities.product_management.services.IdeaService.can_modify_idea')
        mock_service.return_value = False

        with pytest.raises(PermissionDenied):
            authenticated_client.post(
                reverse('product_management:update-idea', 
                       kwargs={'product_slug': product.slug, 'pk': idea.id}),
                {'title': 'Updated Idea'}
            )

@pytest.mark.django_db
class TestVotingSystem:
    def test_vote_requires_authentication(self, client, product):
        idea = Idea(id=1, product=product)
        response = client.post(
            reverse('product_management:cast-vote', kwargs={'pk': idea.id})
        )
        assert response.status_code == 302
        assert '/s/sign-in/' in response.url

    def test_vote_requires_product_visibility_access(self, authenticated_client, product, mocker):
        idea = Idea(id=1, product=product)
        mocker.patch('django.shortcuts.get_object_or_404', return_value=idea)
        mock_service = mocker.patch('apps.capabilities.product_management.services.ProductService.has_product_visibility_access')
        mock_service.return_value = False

        with pytest.raises(PermissionDenied):
            authenticated_client.post(
                reverse('product_management:cast-vote', kwargs={'pk': idea.id})
            )

    def test_successful_vote_toggle(self, authenticated_client, product, person, mocker):
        idea = Idea.objects.create(
            product=product,
            title='Test Idea',
            person=person
        )
        mocker.patch('django.shortcuts.get_object_or_404', return_value=idea)
        mock_product_service = mocker.patch('apps.capabilities.product_management.services.ProductService.has_product_visibility_access')
        mock_product_service.return_value = True
        mock_idea_service = mocker.patch('apps.capabilities.product_management.services.IdeaService.toggle_vote')
        mock_idea_service.return_value = (True, None, 1)

        response = authenticated_client.post(
            reverse('product_management:cast-vote', kwargs={'pk': idea.id})
        )
        
        assert response.status_code == 200
        assert response.json() == {'vote_count': 1}