import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from apps.capabilities.product_management.utils import (
    get_person_data,
    to_dict,
    has_product_access,
    permission_error_message,
    serialize_tree,
    require_product_management_access,
    modify_permission_required
)
from apps.capabilities.product_management.models import Product, ProductArea
from apps.capabilities.talent.models import Person

@pytest.mark.django_db
class TestUtils:
    @pytest.fixture
    def user(self):
        return get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test'
        )

    @pytest.fixture
    def product(self, user):
        person = Person.objects.create(user=user)
        return Product.objects.create(
            name="Test Product",
            short_description="Test description",
            person=person
        )

    @pytest.fixture
    def request_factory(self):
        return RequestFactory()

    def test_get_person_data(self, user):
        # The user object structure is incorrect
        # Need to update either the test or the util function
        data = get_person_data(user)
        assert data['username'] == 'testuser'
        assert data['first_name'] == 'Test'

    def test_to_dict(self, product):
        data = to_dict(product)
        assert isinstance(data, dict)
        assert data['name'] == "Test Product"
        assert 'id' in data

    def test_has_product_access(self, user, product):
        # Test unauthenticated user with global visibility
        product.visibility = Product.Visibility.GLOBAL
        assert has_product_access(None, product) is True
        
        # Test authenticated user with restricted access
        product.visibility = Product.Visibility.RESTRICTED
        product.person = None  # Ensure user is not owner
        assert has_product_access(user, product) is False
        
        # Test org_only visibility
        product.visibility = Product.Visibility.ORG_ONLY
        assert has_product_access(user, product) is False

    def test_permission_error_message(self):
        message = permission_error_message()
        assert isinstance(message, str)
        assert len(message) > 0

    def test_serialize_tree(self, product):
        area = ProductArea.objects.create(
            name="Test Area",
            description="Test description",
            product=product
        )
        tree_data = serialize_tree(area)
        assert tree_data['name'] == "Test Area"
        assert tree_data['description'] == "Test description"
        assert 'children' in tree_data

    def test_require_product_management_access(self, user, product, request_factory):
        @require_product_management_access
        def test_view(request, product_slug):
            return "success"

        request = request_factory.get('/')
        request.user = user
        
        # Add messages middleware
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        response = test_view(request, product.slug)
        assert response == "success"  # or check for redirect based on your implementation

    def test_modify_permission_required(self, user, product):
        class TestView:
            def get_context_data(self):
                return {"can_modify_product": True}
            
            def is_ajax(self):
                return False

            @modify_permission_required
            def test_method(self, request):
                return "success"

        view = TestView()
        result = view.test_method(None)
        assert result == "success"