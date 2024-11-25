# Generated by Django 4.2.2 on 2024-11-01 18:16

from django.db import migrations, models
import django.db.models.deletion
from django.contrib.contenttypes.models import ContentType

def convert_generic_to_explicit(apps, schema_editor):
    Product = apps.get_model('product_management', 'Product')
    Organisation = apps.get_model('commerce', 'Organisation')
    Person = apps.get_model('talent', 'Person')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    
    # Create both ContentTypes if they don't exist
    org_content_type, _ = ContentType.objects.get_or_create(
        app_label='commerce',
        model='organisation'
    )
    
    person_content_type, _ = ContentType.objects.get_or_create(
        app_label='talent',
        model='person'
    )
    
    # Convert organisation-owned products
    for product in Product.objects.filter(content_type_id=org_content_type.id):
        product.organisation_id = product.object_id
        product.person = None
        product.save()
    
    # Convert person-owned products
    for product in Product.objects.filter(content_type_id=person_content_type.id):
        product.person_id = product.object_id
        product.organisation = None
        product.save()

def reverse_convert(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('talent', '0014_delete_status'),
        ('commerce', '0002_initial'),
        ('product_management', '0052_product_visibility'),
    ]

    operations = [
        # First add the new fields while keeping the old ones
        migrations.AddField(
            model_name='product',
            name='organisation',
            field=models.ForeignKey('commerce.Organisation', null=True, blank=True, on_delete=models.SET_NULL, related_name='owned_products'),
        ),
        migrations.AddField(
            model_name='product',
            name='person',
            field=models.ForeignKey('talent.Person', null=True, blank=True, on_delete=models.CASCADE, related_name='owned_products'),
        ),
        
        # Convert the data
        migrations.RunPython(convert_generic_to_explicit, reverse_convert),
        
        # Then remove the old fields
        migrations.RemoveField(
            model_name='product',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='product',
            name='object_id',
        ),
        
        # Finally add the constraint
        migrations.AddConstraint(
            model_name='product',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(person__isnull=True, organisation__isnull=False) |
                    models.Q(person__isnull=False, organisation__isnull=True)
                ),
                name='product_single_owner'
            ),
        ),
    ]
