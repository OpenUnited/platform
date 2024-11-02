from django.db import migrations, models


def migrate_visibility_forward(apps, schema_editor):
    """
    Migrate is_private values to the new visibility field:
    - is_private=True -> ORG_ONLY
    - is_private=False -> GLOBAL
    """
    Product = apps.get_model('product_management', 'Product')
    
    # Update all products based on their is_private value
    Product.objects.filter(is_private=True).update(visibility='ORG_ONLY')
    Product.objects.filter(is_private=False).update(visibility='GLOBAL')


def migrate_visibility_backward(apps, schema_editor):
    """
    Restore is_private values from visibility field if needed
    """
    Product = apps.get_model('product_management', 'Product')
    
    # Restore is_private values
    Product.objects.filter(visibility='ORG_ONLY').update(is_private=True)
    Product.objects.filter(visibility__in=['GLOBAL', 'RESTRICTED']).update(is_private=False)


class Migration(migrations.Migration):
    dependencies = [
        ('product_management', '0051_remove_challenge_tag_delete_tag'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='visibility',
            field=models.CharField(
                choices=[
                    ('GLOBAL', 'Global'),
                    ('ORG_ONLY', 'Organisation Only'),
                    ('RESTRICTED', 'Restricted')
                ],
                default='ORG_ONLY',
                max_length=10
            ),
        ),
        migrations.RunPython(
            migrate_visibility_forward,
            migrate_visibility_backward
        ),
        migrations.RemoveField(
            model_name='product',
            name='is_private',
        ),
    ]