from django.db import migrations


def fix_product_ownership(apps, schema_editor):
    """
    Fix product ownership to ensure single owner
    """
    Product = apps.capabilities.get_model('product_management', 'Product')
    ProductRoleAssignment = apps.capabilities.get_model('security', 'ProductRoleAssignment')
    
    # Fix products with both owners
    products_with_both = Product.objects.filter(
        person__isnull=False,
        organisation__isnull=False
    )
    for product in products_with_both:
        product.person = None
        product.save()

    # Fix products with no owner
    products_with_neither = Product.objects.filter(
        person__isnull=True,
        organisation__isnull=True
    )
    for product in products_with_neither:
        admin_assignment = ProductRoleAssignment.objects.filter(
            product=product,
            role='ADMIN'
        ).first()
        
        if admin_assignment:
            product.person = admin_assignment.person
        else:
            first_assignment = ProductRoleAssignment.objects.filter(
                product=product
            ).first()
            if first_assignment:
                product.person = first_assignment.person
        product.save()


class Migration(migrations.Migration):
    dependencies = [
        ('product_management', '0053_remove_product_content_type_remove_product_object_id_and_more'),
    ]

    operations = [
        migrations.RunPython(
            fix_product_ownership,
            migrations.RunPython.noop
        ),
    ] 