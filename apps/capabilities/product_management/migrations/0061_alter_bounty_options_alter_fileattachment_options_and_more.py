# Generated by Django 4.2.2 on 2024-11-20 13:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product_management', '0060_consolidate_product_fields'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bounty',
            options={'ordering': ('-created_at',), 'verbose_name_plural': 'Bounties'},
        ),
        migrations.AlterModelOptions(
            name='fileattachment',
            options={'verbose_name_plural': 'File Attachments'},
        ),
        migrations.AlterModelOptions(
            name='productarea',
            options={'verbose_name_plural': 'Product Areas'},
        ),
        migrations.AlterModelOptions(
            name='producttree',
            options={'verbose_name_plural': 'Product Trees'},
        ),
    ]
