# Generated by Django 4.2.2 on 2024-11-26 11:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event_hub', '0002_eventlog_is_notification_event_and_more'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='eventlog',
            name='event_hub_e_delete__32a99d_idx',
        ),
        migrations.RemoveField(
            model_name='eventlog',
            name='delete_at',
        ),
        migrations.RemoveField(
            model_name='eventlog',
            name='is_notification_event',
        ),
        migrations.AlterField(
            model_name='eventlog',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='eventlog',
            name='event_type',
            field=models.CharField(max_length=100),
        ),
    ]