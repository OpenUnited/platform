# Generated by Django 4.2.2 on 2024-03-21 23:32

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "product_management",
            "0010_alter_attachment_options_remove_attachment_file_type_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="capability",
            name="video_duration",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="capability",
            name="video_name",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="capability",
            name="video_link",
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
    ]
