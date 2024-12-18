# Generated by Django 4.2.2 on 2024-05-14 10:57

from django.db import migrations, models
import django.db.models.deletion


def forward_func(apps, schema_editor):
    PersonSkill = apps.get_model("talent", "PersonSkill")
    PersonSkill.objects.all().delete()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("talent", "0006_remove_bountyclaim_kind_bountyclaim_status"),
    ]

    operations = [
        migrations.RunPython(forward_func, reverse_func),
        migrations.RemoveField(
            model_name="personskill",
            name="expertise",
        ),
        migrations.AlterField(
            model_name="personskill",
            name="person",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="skills",
                to="talent.person",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="personskill",
            name="skill",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="talent.skill",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="personskill",
            name="expertise",
            field=models.ManyToManyField(to="talent.expertise"),
        ),
    ]
