import pytest
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from apps.talent.models import Person
import uuid
from unittest.mock import patch, Mock

from apps.product_management.models import Product, Challenge, Bounty
from apps.talent.models import Person, Skill, Expertise
from apps.product_management.flows.challenge_authoring.services import ChallengeAuthoringService
from apps.product_management.flows.challenge_authoring.views import ChallengeAuthoringView

@pytest.fixture
def user(db):
    """Create a test user with person"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    user.person = Person.objects.create(
        user=user,
        full_name='Test User',
        preferred_name='Test'
    )
    user.save()
    return user

@pytest.fixture
def product(db, user):
    """Create a test product"""
    return Product.objects.create(
        name='Test Product',
        slug='test-product',
        person=user.person
    )

@pytest.fixture
def valid_challenge_data():
    """Valid challenge creation data"""
    return {
        'title': 'Test Challenge Title',
        'description': 'This is a test challenge description that meets the minimum length requirement for validation.',
        'status': 'draft',
        'priority': 'medium'
    }

@pytest.fixture
def valid_bounties_data():
    """Valid bounties data"""
    return [{
        'title': 'Test Bounty',
        'description': 'Test bounty description',
        'points': 100,
        'skill': 1,
        'expertise': [1, 2]
    }]

@pytest.fixture
def invalid_bounties_data():
    """Invalid bounties data with various validation issues"""
    return [
        {
            'title': '',  # Empty title
            'description': 'Test bounty description',
            'points': 0,  # Invalid points
            'skill': 1,
            'expertise': []  # Empty expertise list
        },
        {
            'title': 'Second Bounty',
            'description': 'Test bounty description',
            'points': 2000,  # Exceeds maximum points
            'skill': 1,
            'expertise': [1]
        }
    ]

@pytest.fixture
def mock_role_service():
    with patch('apps.product_management.flows.challenge_authoring.services.RoleService') as mock:
        instance = mock.return_value
        # Make is_product_manager return True by default and track calls
        instance.is_product_manager = Mock(return_value=True)
        return instance

@pytest.fixture
def person(db, django_user_model):
    """Create a test person"""
    # Create a unique username using a UUID
    unique_id = str(uuid.uuid4())[:8]
    username = f'testuser_{unique_id}'
    
    # First create a User instance
    user = django_user_model.objects.create_user(
        username=username,
        email=f'test_{unique_id}@example.com',
        password='testpass123'
    )
    
    # Then create the Person instance
    person = Person.objects.create(
        user=user,
        full_name="Test User",
        preferred_name="Test",
        points=0
    )
    
    return person

@pytest.fixture(autouse=True)
def setup_user_person(user, person):
    """Ensure user has a person attribute"""
    user.person = person
    user.save()
    return user

@pytest.fixture
def skills(db):
    """Create test skills"""
    return [
        Skill.objects.create(name='Frontend Development'),
        Skill.objects.create(name='Backend Development')
    ]

@pytest.fixture
def expertise_items(db, skills):
    """Create test expertise items"""
    return [
        Expertise.objects.create(
            skill=skills[0],
            name='React',
            fa_icon='fab fa-react',
            selectable=True
        ),
        Expertise.objects.create(
            skill=skills[0],
            name='React Advanced',
            fa_icon='fab fa-react',
            selectable=True
        ),
        Expertise.objects.create(
            skill=skills[1],
            name='Django',
            fa_icon='fab fa-python',
            selectable=True
        )
    ]

@pytest.fixture
def mock_expertise():
    """Mock expertise data for testing"""
    with patch('apps.product_management.flows.challenge_authoring.services.Expertise') as mock:
        mock_instance = Mock()
        mock_instance.objects.filter.return_value = [
            Mock(id=1, name='Test Expertise', description='Test Description')
        ]
        return mock_instance

class TestChallengeAuthoringView:
    def test_view_requires_authentication(self, client, product):
        """Test that unauthenticated users cannot access the view"""
        url = reverse('challenge_create', kwargs={'product_slug': product.slug})
        response = client.get(url)
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_view_requires_person(self, client, user, product):
        """Test that users without person object cannot access the view"""
        user.person = None
        client.force_login(user)
        url = reverse('challenge_create', kwargs={'product_slug': product.slug})
        response = client.get(url)
        assert response.status_code == 403

    def test_view_requires_product_manager(self, client, user, product, mock_role_service):
        """Test that non-managers cannot access the view"""
        mock_role_service.is_product_manager.return_value = False
        client.force_login(user)
        url = reverse('challenge_create', kwargs={'product_slug': product.slug})
        response = client.get(url)
        assert response.status_code == 403

    def test_successful_challenge_creation(
        self, client, user, product, mock_role_service, 
        valid_challenge_data, valid_bounties_data
    ):
        """Test successful challenge creation flow"""
        client.force_login(user)
        url = reverse('challenge_create', kwargs={'product_slug': product.slug})
        
        # Mock service layer
        with patch('apps.product_management.flows.challenge_authoring.views.ChallengeAuthoringService') as mock_service:
            mock_service.return_value.create_challenge.return_value = (
                True, 
                Mock(get_absolute_url=lambda: '/success'), 
                None
            )
            
            response = client.post(
                url,
                data={
                    **valid_challenge_data,
                    'bounties': valid_bounties_data
                },
                content_type='application/json'
            )

        assert response.status_code == 200
        assert response.json()['success'] is True
        assert response.json()['redirect_url'] == '/success'

    def test_bounty_modal_api_endpoints(self, client, user, product, mock_role_service):
        """Test the API endpoints used by BountyModal.js"""
        client.force_login(user)
        
        # Test GET request to bounty modal
        url = reverse('bounty_modal', kwargs={'product_slug': product.slug})
        response = client.get(url)
        assert response.status_code == 200
        assert 'modal-wrap__skills' in response.content.decode()

        # Test POST request with AJAX
        response = client.post(
            url,
            data={
                'title': 'Test Bounty',
                'description': 'Test Description',
                'points': 100,
                'skill_id': 1,
                'expertise_ids': '1,2'  # Match format from BountyModal.js
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        assert response.status_code == 200
        assert response.json()['success'] is True

    def test_permission_checks(self, client, user, product):
        """Test permission requirements"""
        url = reverse('challenge_create', kwargs={'product_slug': product.slug})
        
        # Test unauthenticated
        response = client.get(url)
        assert response.status_code == 302  # Redirects to login
        
        # Test authenticated but not product manager
        client.force_login(user)
        response = client.get(url)
        assert response.status_code == 403

    def test_form_validation(self, client, user, product, mock_role_service):
        """Test form validation in the view"""
        client.force_login(user)
        url = reverse('challenge_create', kwargs={'product_slug': product.slug})
        
        # Test invalid form submission
        response = client.post(url, {
            'title': '',  # Required field
            'bounty-TOTAL_FORMS': '1',
            'bounty-0-title': ''
        })
        assert response.status_code == 200
        assert 'errors' in response.json()

    def test_skills_api(self, client, user, product, mock_role_service):
        """Test skills list and expertise endpoints"""
        client.force_login(user)
        
        # Test skills list
        url = reverse('challenge_skills', kwargs={'product_slug': product.slug})
        response = client.get(url)
        assert response.status_code == 200

    def test_expertise_list(self, client, user, product, skills):
        """Test expertise list retrieval"""
        client.force_login(user)
        url = reverse('skill_expertise', kwargs={
            'product_slug': product.slug,
            'skill_id': skills[0].id
        })
        response = client.get(url)
        assert response.status_code == 200

class TestChallengeAuthoringService:
    @pytest.fixture(autouse=True)
    def setup_service(self, mocker):
        """Setup common service mocks"""
        mock_role_service = mocker.Mock()
        mock_role_service.is_product_manager.return_value = True
        mocker.patch(
            'apps.product_management.flows.challenge_authoring.services.RoleService',
            return_value=mock_role_service
        )

    def test_service_initialization(self, user, product, mock_role_service):
        """Test service initialization with permissions"""
        service = ChallengeAuthoringService(user, product.slug)
        assert service.user == user
        assert service.product == product
        mock_role_service.return_value.is_product_manager.assert_called_once_with(
            person=user.person,
            product=product
        )

    def test_service_initialization_permission_denied(self, user, product, mock_role_service):
        """Test service initialization without permissions"""
        mock_role_service.is_product_manager.return_value = False
        with pytest.raises(PermissionDenied):
            ChallengeAuthoringService(user, product.slug)

    @pytest.mark.django_db
    def test_challenge_creation(self, user, product, valid_challenge_data, valid_bounties_data, skills):
        """Test full challenge creation flow"""
        service = ChallengeAuthoringService(user, product.slug)
        
        # Update bounties data to use actual Skill instances
        bounties = [{
            **bounty,
            'skill': skills[0]  # Use actual Skill instance
        } for bounty in valid_bounties_data]
        
        success, challenge, errors = service.create_challenge(
            valid_challenge_data,
            bounties
        )
        
        assert success is True
        assert challenge is not None
        assert errors is None

    def test_validation_errors(self, user, product, mock_role_service):
        """Test validation error handling"""
        service = ChallengeAuthoringService(user, product.slug)
        
        invalid_data = {
            'title': 'short',  # Too short
            'description': 'too short',  # Too short
            'status': 'invalid',  # Invalid choice
        }
        
        success, challenge, errors = service.create_challenge(invalid_data, [])
        
        assert success is False
        assert challenge is None
        assert errors is not None
        assert 'title' in errors
        assert 'description' in errors
        assert 'status' in errors

    def test_bounty_validation(self, user, product, valid_challenge_data, invalid_bounties_data, mock_role_service):
        """Test bounty validation rules"""
        service = ChallengeAuthoringService(user, product.slug)
        
        success, challenge, errors = service.create_challenge(
            valid_challenge_data,
            invalid_bounties_data
        )
        
        assert success is False
        assert challenge is None
        assert errors is not None
        assert 'bounties' in errors
        assert 'points' in str(errors['bounties'][0])  # Points validation error
        assert 'title' in str(errors['bounties'][0])   # Title validation error
        assert 'points' in str(errors['bounties'][1])  # Max points exceeded

    @pytest.mark.django_db
    def test_transaction_rollback(self, user, product, valid_challenge_data, valid_bounties_data, mock_role_service):
        """Test that failed bounty creation rolls back challenge creation"""
        service = ChallengeAuthoringService(user, product.slug)
        
        # Modify bounties data to cause a failure after challenge creation
        valid_bounties_data[0]['skill_id'] = 999  # Non-existent skill ID
        
        success, challenge, errors = service.create_challenge(
            valid_challenge_data,
            valid_bounties_data
        )
        
        assert success is False
        assert challenge is None
        assert errors is not None
        # Verify no challenge was created (transaction rolled back)
        assert Challenge.objects.count() == 0
        assert Bounty.objects.count() == 0

    @pytest.mark.django_db
    def test_max_bounties_limit(self, user, product, valid_challenge_data, mock_role_service):
        """Test maximum number of bounties per challenge"""
        service = ChallengeAuthoringService(user, product.slug)
        
        # Create 11 bounties (exceeding max limit of 10)
        too_many_bounties = [
            {
                'title': f'Bounty {i}',
                'description': 'Test bounty description',
                'points': 100,
                'skill_id': 1,
                'expertise_ids': [1]
            }
            for i in range(11)
        ]
        
        success, challenge, errors = service.create_challenge(
            valid_challenge_data,
            too_many_bounties
        )
        
        assert success is False
        assert challenge is None
        assert errors is not None
        assert 'bounties' in errors
        assert 'maximum of 10 bounties' in str(errors['bounties'])

    @pytest.mark.django_db
    def test_total_points_limit(self, user, product, valid_challenge_data, mock_role_service):
        """Test total points limit across all bounties"""
        service = ChallengeAuthoringService(user, product.slug)
        
        # Create bounties exceeding total points limit
        high_point_bounties = [
            {
                'title': f'Bounty {i}',
                'description': 'Test bounty description',
                'points': 100,
                'skill_id': 1,
                'expertise_ids': [1]
            }
            for i in range(11)
        ]
        
        success, challenge, errors = service.create_challenge(
            valid_challenge_data,
            high_point_bounties
        )
        
        assert success is False
        assert challenge is None
        assert errors is not None
        assert 'bounties' in errors
        assert 'total points limit' in str(errors['bounties'])

    def test_get_skills_list(self, user, product, skills, mock_role_service):
        """Test skills list retrieval"""
        service = ChallengeAuthoringService(user, product.slug)
        skills_list = service.get_skills_list()
        
        assert len(skills_list) == 2
        assert skills_list[0]['name'] == 'Frontend Development'
        assert 'id' in skills_list[0]

    def test_get_expertise_for_skill(self, user, product, skills, expertise_items, mock_role_service):
        """Test expertise retrieval for a skill"""
        service = ChallengeAuthoringService(user, product.slug)
        expertise_list = service.get_expertise_for_skill(skills[0].id)
        
        assert len(expertise_list) == 2  # Two React expertise levels
        assert expertise_list[0]['name'] == 'React'
        assert expertise_list[0]['level'] == 'BEGINNER'
        assert 'id' in expertise_list[0]

    def test_expertise_ids_format(self, user, product, valid_challenge_data, mock_role_service):
        """Test handling of expertise_ids in both string and list formats"""
        service = ChallengeAuthoringService(user, product.slug)
        
        # Test with string format (from AJAX)
        bounties_string_format = [{
            'title': 'Test Bounty',
            'description': 'Test Description',
            'points': 100,
            'skill_id': 1,
            'expertise_ids': '1,2'
        }]
        
        success, _, _ = service.create_challenge(
            valid_challenge_data,
            bounties_string_format
        )
        assert success is True

        # Test with list format (from regular form)
        bounties_list_format = [{
            'title': 'Test Bounty',
            'description': 'Test Description',
            'points': 100,
            'skill_id': 1,
            'expertise_ids': [1, 2]
        }]
        
        success, _, _ = service.create_challenge(
            valid_challenge_data,
            bounties_list_format
        )
        assert success is True

    def test_validation_rules(self, user, product):
        """Test all validation rules for challenges and bounties"""
        service = ChallengeAuthoringService(user, product.slug)
        
        # Test challenge validation
        invalid_challenge = {
            'title': 'A' * 256,  # Exceeds MAX_TITLE_LENGTH
            'description': 'Too short',  # Less than 50 chars
            'status': 'INVALID_STATUS',
            'priority': 'INVALID_PRIORITY',
            'video_url': 'not-a-url'
        }
        
        errors = service._validate_challenge(invalid_challenge)
        assert len(errors) > 0
        assert any('Title must be less than' in error for error in errors)
        assert any('Description must be at least' in error for error in errors)
        assert any('Invalid status' in error for error in errors)
        assert any('Invalid priority' in error for error in errors)
        assert any('Invalid video URL format' in error for error in errors)

    def test_bounty_validation(self, user, product):
        """Test bounty-specific validation rules"""
        service = ChallengeAuthoringService(user, product.slug)
        
        invalid_bounties = [
            {
                'title': '',
                'description': '',
                'points': 0,
                'skill': None,
                'expertise_ids': []
            }
        ] * 11  # Exceeds MAX_BOUNTIES
        
        errors = service._validate_bounties(invalid_bounties)
        assert any(f'Maximum of {service.MAX_BOUNTIES} bounties' in error for error in errors)

    def test_expertise_validation(self, user, product, mock_expertise):
        """Test expertise validation for bounties"""
        service = ChallengeAuthoringService(user, product.slug)
        
        bounty_data = [{
            'title': 'Test Bounty',
            'description': 'Description',
            'points': 100,
            'skill': 1,
            'expertise_ids': '999'  # Non-existent expertise
        }]
        
        errors = service._validate_bounties(bounty_data)
        assert any('Invalid expertise selection' in error for error in errors)

    def test_cross_validation(self, user, product):
        """Test validation between challenges and bounties"""
        service = ChallengeAuthoringService(user, product.slug)
        
        challenge_data = {
            'status': 'ACTIVE',
            'reward_type': 'POINTS'
        }
        bounties_data = []  # Empty bounties for active challenge
        
        errors = service._validate_challenge_bounty_relationship(
            challenge_data,
            bounties_data
        )
        assert any('Active challenges must have at least one bounty' in error for error in errors)

class TestSkillEndpoints:
    """Test cases for skill and expertise API endpoints"""
    
    def test_skills_list_requires_auth(self, client, product):
        """Test that unauthenticated users cannot access skills list"""
        url = reverse('challenge_skills', kwargs={'product_slug': product.slug})
        response = client.get(url)
        assert response.status_code == 302  # Redirects to login

    def test_skills_list(self, client, user, product):
        """Test successful skills list retrieval"""
        client.force_login(user)
        url = reverse('challenge_skills', kwargs={'product_slug': product.slug})
        response = client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        assert 'skills' in data
        assert len(data['skills']) == 2
        assert data['skills'][0]['name'] == 'Frontend Development'

    def test_expertise_requires_auth(self, client, product, skills):
        """Test that unauthenticated users cannot access expertise list"""
        url = reverse('skill_expertise', kwargs={
            'product_slug': product.slug,
            'skill_id': skills[0].id
        })
        response = client.get(url)
        assert response.status_code == 302  # Redirects to login

    def test_expertise_list(self, client, user, product, skills):
        """Test expertise list retrieval"""
        client.force_login(user)
        url = reverse('skill_expertise', kwargs={
            'product_slug': product.slug,
            'skill_id': skills[0].id
        })
        response = client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert 'expertise' in data
        assert len(data['expertise']) == 2  # Two React expertise levels
        assert data['expertise'][0]['name'] == 'React'
        assert data['expertise'][0]['level'] == 'BEGINNER'

    def test_expertise_invalid_skill(self, client, user, product):
        """Test expertise retrieval with invalid skill ID"""
        client.force_login(user)
        url = reverse('skill_expertise', kwargs={
            'product_slug': product.slug,
            'skill_id': 999
        })
        response = client.get(url)
        assert response.status_code == 404
