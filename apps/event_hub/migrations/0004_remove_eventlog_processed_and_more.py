# Generated by Django 4.2.2 on 2024-11-26 12:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_hub', '0003_remove_eventlog_event_hub_e_delete__32a99d_idx_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='eventlog',
            name='processed',
        ),
        migrations.RemoveField(
            model_name='eventlog',
            name='processing_time',
        ),
    ]
