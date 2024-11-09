import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.capabilities.product_management.forms import (
    ProductForm,
    BountyForm,
    ChallengeForm,
    ProductAreaForm
)

@pytest.mark.django_db
class TestProductForm:
    @pytest.fixture
    def valid_data(self):
        return {
            'name': 'Test Product',
            'short_description': 'A test product',
            'full_description': 'A detailed test product description',
            'visibility': 'GLOBAL',
        }

    def test_valid_form(self, person):
        form_data = {
            'name': 'Test Product',
            'short_description': 'A test product',
            'full_description': 'A detailed test product description',
            'visibility': 'GLOBAL',
            'make_me_owner': True
        }
        form = ProductForm(data=form_data, person=person)
        assert form.is_valid()

    def test_invalid_form_missing_required(self):
        form = ProductForm(data={})
        assert not form.is_valid()
        assert 'name' in form.errors
        assert 'short_description' in form.errors

    def test_form_with_file_upload(self, valid_data):
        file_data = SimpleUploadedFile(
            "test.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        form = ProductForm(
            data=valid_data,
            files={'photo': file_data}
        )
        assert form.is_valid() 