# Generated by Django 4.2.2 on 2024-05-28 09:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("product_management", "0044_alter_challenge_priority_alter_challenge_reward_type"),
        ("talent", "0009_alter_bountydeliveryattempt_kind"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="bountydeliveryattempt",
            name="attachment",
        ),
    ]