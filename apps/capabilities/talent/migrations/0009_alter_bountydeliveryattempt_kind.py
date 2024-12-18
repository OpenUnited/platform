# Generated by Django 4.2.2 on 2024-05-27 19:30

from django.db import migrations, models

NEW = "New"
APPROVED = "Approved"
REJECTED = "Rejected"


def forward_func(apps, schema_editor):
    BountyDeliveryAttempt = apps.get_model("talent", "BountyDeliveryAttempt")
    for attempt in BountyDeliveryAttempt.objects.all():
        if attempt.kind in ["0", 0]:
            attempt.kind = NEW
        elif attempt.kind in ["1", 1]:
            attempt.kind = APPROVED
        elif attempt.kind in ["2", 2]:
            attempt.kind = REJECTED
        attempt.save()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("talent", "0008_expertise_fa_icon"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bountydeliveryattempt",
            name="kind",
            field=models.CharField(
                choices=[("New", "New"), ("Approved", "Approved"), ("Rejected", "Rejected")], default="New"
            ),
        ),
        migrations.RunPython(forward_func, reverse_func),
    ]
