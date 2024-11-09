import pytest
from django.core.exceptions import ValidationError
from apps.capabilities.product_management.models import Product
from django.contrib.auth import get_user_model
from apps.capabilities.talent.models import Person

@pytest.mark.django_db
class TestProductModel:
    def test_product_single_owner_constraint(self, person, organisation):
        """Test that a product cannot have both person and organisation as owners"""
        with pytest.raises(ValidationError):
            Product.objects.create(
                name="Invalid Product",
                short_description="Test",
                person=person,
                organisation=organisation
            )

    def test_product_requires_owner(self):
        """Test that a product must have either person or organisation as owner"""
        with pytest.raises(ValidationError):
            Product.objects.create(
                name="No Owner Product",
                short_description="Test"
            )

    def test_product_owner_property(self, product_with_person, product_with_org, person, organisation):
        """Test the owner property returns correct owner"""
        assert product_with_person.owner == person
        assert product_with_org.owner == organisation

    def test_owner_type_property(self, product_with_person, product_with_org):
        """Test the owner_type property returns correct type"""
        assert product_with_person.owner_type == 'person'
        assert product_with_org.owner_type == 'organisation'

    def test_can_user_manage(self, product_with_person, product_with_org, user, person):
        """Test product management permissions"""
        # Person owner can manage their product
        assert product_with_person.can_user_manage(user) is True

        # Create another user who shouldn't have access
        other_user = get_user_model().objects.create_user(
            username='other',
            email='other@example.com',
            password='pass123'
        )
        other_person = Person.objects.create(user=other_user)
        
        assert product_with_person.can_user_manage(other_user) is False

    def test_visibility_validation(self, person):
        """Test visibility field validation"""
        # Test default visibility
        product = Product.objects.create(
            name="Test Product",
            short_description="Test",
            person=person
        )
        assert product.visibility == Product.Visibility.ORG_ONLY

        # Test setting explicit visibility
        product = Product.objects.create(
            name="Global Product",
            short_description="Test",
            person=person,
            visibility=Product.Visibility.GLOBAL
        )
        assert product.visibility == Product.Visibility.GLOBAL 