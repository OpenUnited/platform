import pytest
from django.contrib.auth import get_user_model
from apps.capabilities.product_management.models import Product, Challenge, Bounty, Idea, Bug, Initiative, ProductContributorAgreementTemplate, ProductArea, ProductTree
from apps.capabilities.product_management.services import (
    ProductService, IdeaService, BugService, ChallengeCreationService,
    ProductManagementService, ContributorAgreementService, ProductAreaService,
    InitiativeService, ChallengeService, ProductTreeService, ProductPeopleService,
    BountyService, ProductContentService
)
from apps.capabilities.talent.models import Person
from apps.capabilities.commerce.models import Organisation
from django.utils import timezone
from apps.common.exceptions import InvalidInputError
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@pytest.fixture
def authenticated_user(db):
    user = User.objects.create_user(username='testuser', password='12345')
    user.person = Person.objects.create(user=user)
    return user

@pytest.mark.django_db
class TestProductService:
    def test_get_visible_products_anonymous(self, client):
        # Create a person for the product
        user = User.objects.create_user(username='owner', password='12345')
        person = Person.objects.create(user=user)
        
        # Create products with different visibility
        global_product = Product.objects.create(
            name="Global Product",
            visibility=Product.Visibility.GLOBAL,
            person=person
        )
        restricted_product = Product.objects.create(
            name="Restricted Product",
            visibility=Product.Visibility.RESTRICTED,
            person=person
        )

        visible_products = ProductService.get_visible_products(None)
        
        assert global_product in visible_products
        assert restricted_product not in visible_products

    def test_get_visible_products_authenticated(self, authenticated_user, mocker):
        global_product = Product.objects.create(
            name="Global Product",
            visibility=Product.Visibility.GLOBAL,
            person=authenticated_user.person
        )
        restricted_product = Product.objects.create(
            name="Restricted Product",
            visibility=Product.Visibility.RESTRICTED,
            person=authenticated_user.person
        )
        
        # Mock RoleService to return restricted product
        mocker.patch(
            'apps.capabilities.security.services.RoleService.get_user_products',
            return_value=Product.objects.filter(id=restricted_product.id)
        )

        visible_products = ProductService.get_visible_products(authenticated_user)
        
        assert global_product in visible_products
        assert restricted_product in visible_products

    def test_convert_youtube_link_valid(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = ProductService.convert_youtube_link_to_embed(url)
        assert result == "https://www.youtube.com/embed/dQw4w9WgXcQ"

    def test_convert_youtube_link_invalid(self):
        url = "https://not-youtube.com/watch?v=123"
        
        # The InvalidInputError should be raised
        with pytest.raises(InvalidInputError, match="Not a valid YouTube URL"):
            ProductService.convert_youtube_link_to_embed(url)

@pytest.mark.django_db
class TestIdeaService:
    def test_create_idea(self, authenticated_user):
        product = Product.objects.create(
            name="Test Product",
            person=authenticated_user.person
        )
        form_data = {
            "title": "Test Idea",
            "description": "Idea description"
        }
        
        success, error, idea = IdeaService.create_idea(form_data, authenticated_user.person, product)
        
        assert success is True
        assert error is None
        assert idea.title == "Test Idea"
        assert idea.person == authenticated_user.person

    def test_toggle_vote(self, authenticated_user):
        product = Product.objects.create(
            name="Test Product",
            person=authenticated_user.person
        )
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
        product = Product.objects.create(
            name="Test Product",
            person=authenticated_user.person
        )
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
        product = Product.objects.create(
            name="Test Product",
            person=authenticated_user.person
        )
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
        product = Product.objects.create(
            name="Test Product",
            person=authenticated_user.person
        )
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

    def test_challenge_creation_rollback(self, authenticated_user):
        product = Product.objects.create(
            name="Test Product",
            person=authenticated_user.person
        )
        
        challenge_data = {
            "title": "Test Challenge",
            "product": product
        }
        bounties_data = [{
            "title": "Test Bounty",
            "points": -100  # Invalid points to trigger error
        }]

        service = ChallengeCreationService(
            challenge_data=challenge_data,
            bounties_data=bounties_data,
            user=authenticated_user
        )
        
        with pytest.raises(InvalidInputError):
            service.process_submission()
        
        # Verify nothing was created due to rollback
        assert Challenge.objects.count() == 0
        assert Bounty.objects.count() == 0

@pytest.mark.django_db
class TestProductManagementService:
    def test_create_product_success(self, authenticated_user):
        form_data = {
            "name": "New Product",
            "slug": "new-product",
            "visibility": Product.Visibility.GLOBAL,
        }
        
        product = ProductManagementService.create_product(
            form_data,
            authenticated_user.person
        )
        
        assert product.name == "New Product"
        assert product.person == authenticated_user.person

    def test_create_product_invalid_data(self, authenticated_user):
        form_data = {
            # Missing required name
            "visibility": Product.Visibility.GLOBAL,
        }
        
        with pytest.raises(InvalidInputError) as exc:
            ProductManagementService.create_product(
                form_data,
                authenticated_user.person
            )
        assert "name is required" in str(exc.value)

@pytest.mark.django_db
class TestContributorAgreementService:
    def test_create_template(self, authenticated_user):
        product = Product.objects.create(
            name="Test Product",
            person=authenticated_user.person
        )
        form_data = {
            "title": "Test Template",
            "content": "Agreement content",
            "product_id": product.id,
            "effective_date": timezone.now()
        }

        success, error, template = ContributorAgreementService.create_template(
            form_data,
            authenticated_user.person
        )
        
        assert success is True
        assert error is None
        assert template.title == "Test Template"
        assert template.created_by == authenticated_user.person

@pytest.mark.django_db
class TestProductAreaService:
    def test_create_area(self):
        user = User.objects.create_user(username='owner', password='12345')
        person = Person.objects.create(user=user)
        
        product = Product.objects.create(
            name="Test Product",
            person=person
        )
        product_tree = ProductTree.objects.create(
            name="Test Tree",
            product=product
        )
        form_data = {
            "name": "Test Area",
            "product_tree": product_tree
        }

        success, error, area = ProductAreaService.create_area(form_data)
        
        assert success is True
        assert error is None
        assert area.name == "Test Area"
        assert area.product_tree.product == product

    def test_update_area(self, authenticated_user):
        product = Product.objects.create(
            name="Test Product",
            person=authenticated_user.person
        )
        product_tree = ProductTree.objects.create(
            name="Test Tree",
            product=product
        )
        # Create as root node since it's using treebeard
        area = ProductArea.add_root(
            name="Original Area",
            product_tree=product_tree
        )
        
        form_data = {
            "name": "Updated Area"
        }

        success, error = ProductAreaService.update_area(area, form_data)
        
        assert success is True
        assert error is None
        area.refresh_from_db()
        assert area.name == "Updated Area"

@pytest.mark.django_db
class TestInitiativeService:
    def test_create_initiative(self, authenticated_user):
        product = Product.objects.create(
            name="Test Product",
            person=authenticated_user.person
        )
        form_data = {
            "name": "Test Initiative",
            "description": "Initiative Description",
            "product": product,
            "status": Initiative.InitiativeStatus.ACTIVE
        }

        success, error, initiative = InitiativeService.create_initiative(
            form_data,
            authenticated_user.person
        )
        assert success is True

    def test_get_product_initiatives(self, authenticated_user):
        product = Product.objects.create(
            name="Test Product",
            person=authenticated_user.person
        )
        Initiative.objects.create(
            name="Test Initiative",
            product=product,
            status=Initiative.InitiativeStatus.ACTIVE
        )

@pytest.mark.django_db
class TestBountyService:
    def test_get_visible_bounties(self, authenticated_user):
        product = Product.objects.create(
            name="Test Product",
            visibility=Product.Visibility.GLOBAL,
            person=authenticated_user.person
        )
        challenge = Challenge.objects.create(
            title="Test Challenge",
            product=product
        )
        bounty = Bounty.objects.create(
            title="Test Bounty",
            challenge=challenge,
            points=100
        )

        visible_bounties = BountyService.get_visible_bounties(authenticated_user)
        
        assert bounty in visible_bounties

    def test_get_product_bounties(self, authenticated_user):
        product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            person=authenticated_user.person
        )
        challenge = Challenge.objects.create(
            title="Test Challenge",
            product=product
        )
        bounty = Bounty.objects.create(
            title="Test Bounty",
            challenge=challenge,
            points=100
        )

        product_bounties = BountyService.get_product_bounties("test-product")
        
        assert bounty in product_bounties

@pytest.mark.django_db
class TestProductContentService:
    def test_get_product_content(self, authenticated_user):
        product = Product.objects.create(
            name="Test Product",
            person=authenticated_user.person
        )
        
        # Create test content
        idea = Idea.objects.create(
            title="Test Idea",
            product=product,
            person=authenticated_user.person
        )
        bug = Bug.objects.create(
            title="Test Bug",
            product=product,
            person=authenticated_user.person
        )
        
        content = ProductContentService.get_product_content(product)
        
        assert idea in content['ideas']
        assert bug in content['bugs']
        assert len(content['initiatives']) == 0
        assert len(content['challenges']) == 0

    def test_get_content_stats(self, authenticated_user):
        product = Product.objects.create(
            name="Test Product",
            person=authenticated_user.person
        )
        
        # Create test content
        Idea.objects.create(
            title="Test Idea",
            product=product,
            person=authenticated_user.person
        )
        Bug.objects.create(
            title="Test Bug",
            product=product,
            person=authenticated_user.person
        )
        
        stats = ProductContentService.get_content_stats(product)
        
        assert stats['idea_count'] == 1
        assert stats['bug_count'] == 1
        assert stats['initiative_count'] == 0
        assert stats['challenge_count'] == 0
