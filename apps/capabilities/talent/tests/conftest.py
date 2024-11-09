from apps.common.tests.conftest import *

@pytest.fixture
def user_data():
    """Base data for creating users"""
    return {
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'testpass123'
    }

@pytest.fixture
def person_data():
    """Base data for creating person profiles"""
    return {
        'full_name': 'Test User',
        'preferred_name': 'Tester',
        'points': 0  # Starting as DRONE
    }

@pytest.fixture
def user(db, user_data):
    """Create a basic user without person profile"""
    User = get_user_model()
    return User.objects.create_user(**user_data)

@pytest.fixture
def person(db, user, person_data):
    """Create a person profile with associated user"""
    from apps.capabilities.talent.models import Person
    
    person_data['user'] = user
    return Person.objects.create(**person_data)

@pytest.fixture
def authenticated_user(user, person, client):
    """Returns an authenticated user with person profile"""
    client.force_login(user)
    return user
