import pytest
from django.template import Context, Template
from apps.capabilities.product_management.templatetags.custom_filters import multiply
from apps.capabilities.product_management.templatetags.product_management_tags import register as product_tags
from apps.capabilities.product_management.templatetags.summary_tags import register as summary_tags
from apps.capabilities.product_management.templatetags.tree_macros import register as tree_tags
from apps.capabilities.product_management.models import Product, Challenge
from apps.capabilities.talent.models import Person

@pytest.mark.django_db
class TestCustomFilters:
    def test_multiply_valid_numbers(self):
        assert multiply(5, 3) == 15
        assert multiply("5", "3") == 15
        assert multiply(0, 100) == 0

    def test_multiply_invalid_input(self):
        assert multiply("invalid", 3) == ''
        assert multiply(5, "invalid") == ''
        assert multiply(None, None) == ''

@pytest.mark.django_db
class TestProductManagementTags:
    @pytest.fixture
    def product(self, user):
        person = Person.objects.create(user=user)
        return Product.objects.create(
            name="Test Product",
            short_description="Test description",
            person=person
        )

    def test_template_rendering(self, product):
        template = Template(
            '{% load product_management_tags %}'
            '{% load custom_filters %}'
        )
        context = Context({'product': product})
        rendered = template.render(context)
        assert rendered.strip() == ''  # Just testing if it loads without errors

@pytest.mark.django_db
class TestSummaryTags:
    @pytest.fixture
    def product(self, user):
        person = Person.objects.create(user=user)
        return Product.objects.create(
            name="Test Product",
            short_description="Test description",
            person=person
        )

    @pytest.fixture
    def challenge(self, product):
        return Challenge.objects.create(
            title="Test Challenge",
            description="Test description",
            product=product
        )

    def test_template_rendering(self, product, challenge):
        template = Template(
            '{% load summary_tags %}'
        )
        context = Context({
            'product': product,
            'challenge': challenge
        })
        rendered = template.render(context)
        assert rendered.strip() == ''  # Just testing if it loads without errors

@pytest.mark.django_db
class TestTreeMacros:
    @pytest.fixture
    def product(self, user):
        person = Person.objects.create(user=user)
        return Product.objects.create(
            name="Test Product",
            short_description="Test description",
            person=person
        )

    def test_template_rendering(self, product):
        template = Template(
            '{% load tree_macros %}'
        )
        context = Context({'product': product})
        rendered = template.render(context)
        assert rendered.strip() == ''  # Just testing if it loads without errors