# Generated by Django 4.2.2 on 2024-05-28 14:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("product_management", "0044_alter_challenge_priority_alter_challenge_reward_type"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Attachment",
        ),
    ]
