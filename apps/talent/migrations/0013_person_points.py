# Generated by Django 4.2.2 on 2024-05-31 21:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("talent", "0012_alter_bountydeliveryattempt_attachments_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="points",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
