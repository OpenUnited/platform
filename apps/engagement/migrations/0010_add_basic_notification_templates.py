from django.db import migrations

def add_basic_templates(apps, schema_editor):
    EmailNotificationTemplate = apps.get_model('engagement', 'EmailNotificationTemplate')
    AppNotificationTemplate = apps.get_model('engagement', 'AppNotificationTemplate')
    
    # Basic templates for product.created
    EmailNotificationTemplate.objects.create(
        event_type='product.created',
        title='New Product Created: {product_name}',
        template='You have successfully created a new product: {product_name}. View it here: {product_url}',
        permitted_params='product_name,product_url'
    )
    
    AppNotificationTemplate.objects.create(
        event_type='product.created',
        title='New Product Created: {product_name}',
        template='You have successfully created a new product: {product_name}. <a href="{product_url}">View product</a>',
        permitted_params='product_name,product_url'
    )

    # Basic templates for product.updated
    EmailNotificationTemplate.objects.create(
        event_type='product.updated',
        title='Product Updated: {product_name}',
        template='The product {product_name} has been updated. View the changes here: {product_url}',
        permitted_params='product_name,product_url'
    )
    
    AppNotificationTemplate.objects.create(
        event_type='product.updated',
        title='Product Updated: {product_name}',
        template='The product {product_name} has been updated. <a href="{product_url}">View changes</a>',
        permitted_params='product_name,product_url'
    )

    # Basic templates for bounty.claimed
    EmailNotificationTemplate.objects.create(
        event_type='bounty.claimed',
        title='Bounty Claimed: {bounty_title}',
        template='A bounty you created has been claimed: {bounty_title}. View the claim here: {bounty_url}',
        permitted_params='bounty_title,claimer_name,bounty_url'
    )
    
    AppNotificationTemplate.objects.create(
        event_type='bounty.claimed',
        title='Bounty Claimed: {bounty_title}',
        template='{claimer_name} has claimed your bounty: {bounty_title}. <a href="{bounty_url}">View claim</a>',
        permitted_params='bounty_title,claimer_name,bounty_url'
    )

def remove_basic_templates(apps, schema_editor):
    EmailNotificationTemplate = apps.get_model('engagement', 'EmailNotificationTemplate')
    AppNotificationTemplate = apps.get_model('engagement', 'AppNotificationTemplate')
    
    # Remove templates
    EmailNotificationTemplate.objects.filter(event_type__in=['product.created', 'bounty.claimed']).delete()
    AppNotificationTemplate.objects.filter(event_type__in=['product.created', 'bounty.claimed']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('engagement', '0009_remove_appnotification_engagement__event_i_5298f0_idx_and_more'),
    ]

    operations = [
        migrations.RunPython(add_basic_templates, remove_basic_templates),
    ]