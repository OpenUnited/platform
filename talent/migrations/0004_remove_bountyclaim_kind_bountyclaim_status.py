# Generated by Django 4.2.2 on 2024-04-11 15:14

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("talent", "0003_alter_bountyclaim_kind"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="bountyclaim",
            name="kind",
        ),
        migrations.AddField(
            model_name="bountyclaim",
            name="status",
            field=models.CharField(
                choices=[
                    ("Requested", "Requested"),
                    ("Rejected", "Rejected"),
                    ("Contributed", "Contributed"),
                    ("Completed", "Completed"),
                    ("Failed", "Failed"),
                ],
                default="Requested",
                max_length=255,
            ),
        ),
    ]