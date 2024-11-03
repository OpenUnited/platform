from django.db import migrations

def migrate_roles_forward(apps, schema_editor):
    ProductRoleAssignment = apps.get_model('security', 'ProductRoleAssignment')
    
    # Update 'Contributor' to 'Member'
    ProductRoleAssignment.objects.filter(role='Contributor').update(role='Member')

def migrate_roles_backward(apps, schema_editor):
    ProductRoleAssignment = apps.get_model('security', 'ProductRoleAssignment')
    
    # Revert 'Member' back to 'Contributor'
    ProductRoleAssignment.objects.filter(role='Member').update(role='Contributor')

class Migration(migrations.Migration):
    dependencies = [
        ('security', '0011_organisationpersonroleassignment_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_roles_forward, migrate_roles_backward),
    ]