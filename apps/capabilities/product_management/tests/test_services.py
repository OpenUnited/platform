import pytest
from django.contrib.auth import get_user_model
from apps.capabilities.product_management.services import ProductService
from apps.capabilities.product_management.models import Product
from apps.capabilities.talent.models import Person

@pytest.mark.django_db
class TestProductService:
    @pytest.fixture
    def user(self):
        return get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def product_data(self):
        return {
            'name': 'Test Product',
            'short_description': 'A test product',
            'visibility': Product.Visibility.GLOBAL
        }

    def test_create_product(self, user, product_data):
        # Create Person first
        person = Person.objects.create(user=user)
        
        product = Product.objects.create(
            name=product_data['name'],
            short_description=product_data['short_description'],
            visibility=product_data['visibility'],
            person=person
        )
        assert product.name == product_data['name']
        assert product.short_description == product_data['short_description']
        assert product.visibility == Product.Visibility.GLOBAL

    def test_get_product_by_slug(self, user, product_data):
        product = Product.objects.create(
            name=product_data['name'],
            short_description=product_data['short_description'],
            visibility=product_data['visibility'],
            person=user.person
        )
        retrieved_product = Product.objects.get(slug=product.slug)
        assert retrieved_product == product