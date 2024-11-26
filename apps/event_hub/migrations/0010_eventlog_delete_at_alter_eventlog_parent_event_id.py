# Generated by Django 4.2.2 on 2024-11-26 19:03

from django.db import migrations, models

def skip_if_fields_exist(apps, schema_editor):
    # Get the database connection
    connection = schema_editor.connection
    
    with connection.cursor() as cursor:
        # Check if fields exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'event_hub_eventlog' 
            AND column_name IN ('delete_at', 'parent_event_id');
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Only create fields that don't exist
        if 'delete_at' not in existing_columns:
            cursor.execute(
                "ALTER TABLE event_hub_eventlog ADD COLUMN delete_at timestamp with time zone NULL"
            )
        if 'parent_event_id' not in existing_columns:
            cursor.execute(
                "ALTER TABLE event_hub_eventlog ADD COLUMN parent_event_id integer NULL"
            )

class Migration(migrations.Migration):
    dependencies = [
        ('event_hub', '0009_remove_processing_time_if_exists'),
    ]

    operations = [
        migrations.RunPython(skip_if_fields_exist, migrations.RunPython.noop),
    ]
