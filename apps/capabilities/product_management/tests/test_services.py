import pytest
from django.contrib.auth import get_user_model
from apps.capabilities.product_management.models import Product, Challenge, Bounty, Idea, Bug, Initiative
from apps.capabilities.product_management.services import (
    ProductService, IdeaService, BugService, ChallengeCreationService,
    ProductManagementService
)
from apps.capabilities.talent.models import Person

User = get_user_model()

@pytest.mark.django_db
class TestProductService:
    def test_get_visible_products_anonymous(self, client):
        # Create products with different visibility
        global_product = Product.objects.create(
            name="Global Product",
            visibility=Product.Visibility.GLOBAL
        )
        restricted_product = Product.objects.create(
            name="Restricted Product",
            visibility=Product.Visibility.RESTRICTED
        )

        visible_products = ProductService.get_visible_products(None)
        
        assert global_product in visible_products
        assert restricted_product not in visible_products

    def test_get_visible_products_authenticated(self, authenticated_user, mocker):
        global_product = Product.objects.create(
            name="Global Product",
            visibility=Product.Visibility.GLOBAL
        )
        restricted_product = Product.objects.create(
            name="Restricted Product",
            visibility=Product.Visibility.RESTRICTED
        )
        
        # Mock RoleService to return restricted product
        mocker.patch(
            'apps.capabilities.security.services.RoleService.get_user_products',
            return_value=Product.objects.filter(id=restricted_product.id)
        )

        visible_products = ProductService.get_visible_products(authenticated_user)
        
        assert global_product in visible_products
        assert restricted_product in visible_products

@pytest.mark.django_db
class TestIdeaService:
    def test_create_idea(self, authenticated_user):
        product = Product.objects.create(name="Test Product")
        person = authenticated_user.person
        form_data = {
            "title": "Test Idea",
            "description": "Test Description"
        }

        success, error, idea = IdeaService.create_idea(form_data, person, product)
        
        assert success is True
        assert error is None
        assert idea.title == "Test Idea"
        assert idea.person == person
        assert idea.product == product

    def test_toggle_vote(self, authenticated_user):
        product = Product.objects.create(name="Test Product")
        idea = Idea.objects.create(
            title="Test Idea",
            product=product,
            person=authenticated_user.person
        )

        # Test adding vote
        success, error, count = IdeaService.toggle_vote(idea, authenticated_user)
        assert success is True
        assert count == 1

        # Test removing vote
        success, error, count = IdeaService.toggle_vote(idea, authenticated_user)
        assert success is True
        assert count == 0

@pytest.mark.django_db
class TestBugService:
    def test_create_bug(self, authenticated_user):
        product = Product.objects.create(name="Test Product")
        person = authenticated_user.person
        form_data = {
            "title": "Test Bug",
            "description": "Bug Description"
        }

        success, error, bug = BugService.create_bug(form_data, person, product)
        
        assert success is True
        assert error is None
        assert bug.title == "Test Bug"
        assert bug.person == person
        assert bug.product == product

    def test_can_modify_bug(self, authenticated_user):
        product = Product.objects.create(name="Test Product")
        bug = Bug.objects.create(
            title="Test Bug",
            product=product,
            person=authenticated_user.person
        )

        assert BugService.can_modify_bug(bug, authenticated_user.person) is True
        
        other_person = Person.objects.create(user=User.objects.create(username="other"))
        assert BugService.can_modify_bug(bug, other_person) is False

@pytest.mark.django_db
class TestChallengeCreationService:
    def test_create_challenge_with_bounties(self, authenticated_user):
        product = Product.objects.create(name="Test Product")
        challenge_data = {
            "title": "Test Challenge",
            "description": "Challenge Description",
            "product": product
        }
        bounties_data = [{
            "title": "Test Bounty",
            "description": "Bounty Description",
            "points": 100
        }]

        service = ChallengeCreationService(
            challenge_data=challenge_data,
            bounties_data=bounties_data,
            user=authenticated_user
        )
        
        success, error = service.process_submission()
        
        assert success is True
        assert error is None
        
        challenge = Challenge.objects.first()
        assert challenge.title == "Test Challenge"
        assert challenge.bounty_set.count() == 1
        assert challenge.bounty_set.first().title == "Test Bounty"

@pytest.mark.django_db
class TestProductManagementService:
    def test_create_product(self, authenticated_user):
        form_data = {
            "name": "New Product",
            "slug": "new-product",
            "visibility": Product.Visibility.GLOBAL
        }

        success, error, product = ProductManagementService.create_product(
            form_data,
            authenticated_user.person
        )
        
        assert success is True
        assert error is None
        assert product.name == "New Product"
        assert product.created_by == authenticated_user.person

    def test_update_product(self, authenticated_user):
        product = Product.objects.create(
            name="Original Name",
            created_by=authenticated_user.person
        )
        
        form_data = {
            "name": "Updated Name"
        }

        success, error = ProductManagementService.update_product(product, form_data)
        
        assert success is True
        assert error is None
        product.refresh_from_db()
        assert product.name == "Updated Name"
