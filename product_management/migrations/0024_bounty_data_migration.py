# Generated by Django 4.2.2 on 2024-04-20 08:29

from django.db import migrations, models


def forward_func(apps, schema_editor):
    Bounty = apps.get_model("product_management.Bounty")
    for bounty in Bounty.objects.all():
        expertise_as_str = ", ".join(
            [exp.name.title() for exp in bounty.expertise.all()]
        )
        skill_name = ""
        if expertise_as_str:
            expertise_as_str = f"({expertise_as_str})"

        if bounty.skill:
            skill_name = bounty.skill.name

        bounty.title = (
            f"{skill_name} {expertise_as_str} - {bounty.challenge.title}"
        )
        bounty.save()


def backward_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("product_management", "0023_bounty_title"),
    ]
    operations = [
        migrations.RunPython(forward_func, backward_func),
        migrations.AlterField(
            model_name="bounty",
            name="title",
            field=models.CharField(max_length=400),
        ),
    ]
