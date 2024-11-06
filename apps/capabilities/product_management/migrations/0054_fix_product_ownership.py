from django.db import migrations


def fix_product_ownership(apps, schema_editor):
    """
    Fix product ownership to ensure single owner
    """
    Product = apps.get_model('product_management', 'Product')
    ProductRoleAssignment = apps.get_model('security', 'ProductRoleAssignment')
    
    # Fix products with both person and organisation
    products_to_fix = Product.objects.filter(
        organisation__isnull=False,
        person__isnull=False
    )
    for product in products_to_fix:
        # Choose which one to keep based on your business logic
        product.person = None  # or product.organisation = None
        product.save()


def reverse_fix(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('product_management', '0053_remove_product_content_type_remove_product_object_id_and_more'),
        ('security', '0001_initial'),  # Add this dependency if needed
    ]

    operations = [
        migrations.RunPython(fix_product_ownership, reverse_fix),
    ] 