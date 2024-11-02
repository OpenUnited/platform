import pytest
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from unittest.mock import Mock, patch

from apps.security.services import RoleService
from apps.product_management.models import Product, Challenge, Bounty
from apps.talent.models import Person
from apps.skills.models import Skill, Expertise
from ..services import ChallengeAuthoringService
from ..views import ChallengeAuthoringView

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
        first_name='Test',
        last_name='User'
    )
    return user

@pytest.fixture
def product(db):
    """Create a test product"""
    return Product.objects.create(
        name='Test Product',
        slug='test-product'
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
    return [
        {
            'title': 'First Bounty',
            'description': 'Test bounty description',
            'points': 100,
            'skill_id': 1,
            'expertise_ids': [1, 2]
        }
    ]

@pytest.fixture
def invalid_bounties_data():
    """Invalid bounties data with various validation issues"""
    return [
        {
            'title': '',  # Empty title
            'description': 'Test bounty description',
            'points': 0,  # Invalid points
            'skill_id': 1,
            'expertise_ids': []
        },
        {
            'title': 'Second Bounty',
            'description': 'Test bounty description',
            'points': 2000,  # Exceeds maximum points
            'skill_id': 1,
            'expertise_ids': [1]
        }
    ]

@pytest.fixture
def mock_role_service():
    """Mock RoleService for permission checks"""
    with patch('apps.security.services.RoleService') as mock_service:
        mock_service.is_product_manager.return_value = True
        mock_service.is_product_admin.return_value = False
        yield mock_service

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
            level='BEGINNER'
        ),
        Expertise.objects.create(
            skill=skills[0],
            name='React',
            level='INTERMEDIATE'
        ),
        Expertise.objects.create(
            skill=skills[1],
            name='Django',
            level='INTERMEDIATE'
        )
    ]

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

class TestChallengeAuthoringService:
    def test_service_initialization(self, user, product, mock_role_service):
        """Test service initialization with permissions"""
        service = ChallengeAuthoringService(user, product.slug)
        assert service.user == user
        assert service.product == product
        mock_role_service.is_product_manager.assert_called_once_with(
            person=user.person,
            product=product
        )

    def test_service_initialization_permission_denied(self, user, product, mock_role_service):
        """Test service initialization without permissions"""
        mock_role_service.is_product_manager.return_value = False
        with pytest.raises(PermissionDenied):
            ChallengeAuthoringService(user, product.slug)

    @pytest.mark.django_db
    def test_challenge_creation(self, user, product, valid_challenge_data, valid_bounties_data):
        """Test full challenge creation flow"""
        with patch('apps.security.services.RoleService') as mock_role_service:
            mock_role_service.is_product_manager.return_value = True
            service = ChallengeAuthoringService(user, product.slug)
            
            success, challenge, errors = service.create_challenge(
                valid_challenge_data,
                valid_bounties_data
            )

        assert success is True
        assert errors is None
        assert isinstance(challenge, Challenge)
        assert challenge.title == valid_challenge_data['title']
        assert challenge.created_by == user
        assert challenge.product == product
        
        # Verify bounty creation
        bounties = Bounty.objects.filter(challenge=challenge)
        assert bounties.count() == len(valid_bounties_data)
        bounty = bounties.first()
        assert bounty.title == valid_bounties_data[0]['title']
        assert bounty.points == valid_bounties_data[0]['points']

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

class TestSkillEndpoints:
    """Test cases for skill and expertise API endpoints"""
    
    def test_skills_list_requires_auth(self, client):
        """Test that unauthenticated users cannot access skills list"""
        url = reverse('challenge_skills')
        response = client.get(url)
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_skills_list(self, client, user, skills):
        """Test successful skills list retrieval"""
        client.force_login(user)
        url = reverse('challenge_skills')
        response = client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        assert 'skills' in data
        assert len(data['skills']) == 2
        assert data['skills'][0]['name'] == 'Frontend Development'

    def test_expertise_requires_auth(self, client, skills):
        """Test that unauthenticated users cannot access expertise list"""
        url = reverse('skill_expertise', kwargs={'skill_id': skills[0].id})
        response = client.get(url)
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_expertise_list(self, client, user, skills, expertise_items):
        """Test successful expertise list retrieval"""
        client.force_login(user)
        url = reverse('skill_expertise', kwargs={'skill_id': skills[0].id})
        response = client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        assert 'expertise' in data
        assert len(data['expertise']) == 2  # Two React expertise levels
        assert data['expertise'][0]['name'] == 'React'
        assert data['expertise'][0]['level'] == 'BEGINNER'

    def test_expertise_invalid_skill(self, client, user, skills):
        """Test expertise retrieval with invalid skill ID"""
        client.force_login(user)
        url = reverse('skill_expertise', kwargs={'skill_id': 999})  # Non-existent ID
        response = client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        assert 'expertise' in data
        assert len(data['expertise']) == 0  # Empty list for invalid skill
