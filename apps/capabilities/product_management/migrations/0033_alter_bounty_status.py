# Generated by Django 4.2.2 on 2024-05-20 15:08

from django.db import migrations, models


def forward_func(apps, schema_editor):
    Bounty = apps.capabilities.get_model("product_management", "Bounty")

    for bounty in Bounty.objects.all():
        status = int(bounty.status)
        if status == 2:
            bounty.status = "Available"
        elif status == 3:
            bounty.status = "Claimed"
        elif status == 4:
            bounty.status = "Completed"
        elif status == 5:
            bounty.status = "In Review"
        bounty.save()

    Bounty.objects.filter(status__in=["0", "1", 0, 1]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("product_management", "0032_merge_20240515_0713"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bounty",
            name="status",
            field=models.CharField(
                choices=[
                    ("Available", "Available"),
                    ("Claimed", "Claimed"),
                    ("In Review", "In Review"),
                    ("Completed", "Completed"),
                    ("Cancelled", "Cancelled"),
                ],
                default="Available",
                max_length=255,
            ),
        ),
        migrations.RunPython(forward_func, migrations.RunPython.noop),
    ]
