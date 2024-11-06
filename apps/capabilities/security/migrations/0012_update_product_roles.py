from django.db import migrations

def migrate_roles_forward(apps, schema_editor):
    ProductRoleAssignment = apps.get_model('security', 'ProductRoleAssignment')
    Product = apps.get_model('product_management', 'Product')
    Person = apps.get_model('talent', 'Person')

    # Update 'Contributor' to 'Member'
    ProductRoleAssignment.objects.filter(role='Contributor').update(role='Member')

def migrate_roles_backward(apps, schema_editor):
    ProductRoleAssignment = apps.get_model('security', 'ProductRoleAssignment')
    
    # Revert 'Member' back to 'Contributor'
    ProductRoleAssignment.objects.filter(role='Member').update(role='Contributor')

class Migration(migrations.Migration):
    dependencies = [
        ('security', '0011_organisationpersonroleassignment_and_more'),
        ('product_management', '0058_product_product_man_slug_74fe12_idx_and_more'),
        ('talent', '0001_initial'),  # Add other dependencies as needed
    ]

    operations = [
        migrations.RunPython(migrate_roles_forward, migrate_roles_backward),
    ]