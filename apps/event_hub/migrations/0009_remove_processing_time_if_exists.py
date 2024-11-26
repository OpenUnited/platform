from django.db import migrations

def remove_processing_time_if_exists(apps, schema_editor):
    # Get the database connection
    connection = schema_editor.connection
    
    with connection.cursor() as cursor:
        # Check if processing_time column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'event_hub_eventlog' 
            AND column_name = 'processing_time';
        """)
        
        if cursor.fetchone():
            # Column exists, so drop it
            cursor.execute(
                "ALTER TABLE event_hub_eventlog DROP COLUMN processing_time"
            )

class Migration(migrations.Migration):
    dependencies = [
        ('event_hub', '0008_remove_processed_if_exists'),
    ]

    operations = [
        migrations.RunPython(remove_processing_time_if_exists, migrations.RunPython.noop),
    ]