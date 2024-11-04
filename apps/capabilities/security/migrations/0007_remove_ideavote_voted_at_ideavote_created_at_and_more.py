# Generated by Django 4.2.2 on 2024-05-16 04:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("security", "0006_alter_ideavote_voter"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="ideavote",
            name="voted_at",
        ),
        migrations.AddField(
            model_name="ideavote",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name="ideavote",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]