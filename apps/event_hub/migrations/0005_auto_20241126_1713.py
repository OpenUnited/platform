from django.db import migrations, models
from django.db.utils import ProgrammingError

def check_and_create_field(apps, schema_editor):
    # Get the database connection
    connection = schema_editor.connection
    
    with connection.cursor() as cursor:
        # Check if column exists using information_schema (safer approach)
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'event_hub_eventlog' 
            AND column_name = 'parent_event_id';
        """)
        
        if not cursor.fetchone():
            # Column doesn't exist, so add it
            cursor.execute(
                "ALTER TABLE event_hub_eventlog ADD COLUMN parent_event_id integer NULL"
            )

class Migration(migrations.Migration):
    dependencies = [
        ('event_hub', '0004_remove_eventlog_processed_and_more'),
    ]

    operations = [
        migrations.RunPython(check_and_create_field, migrations.RunPython.noop),
    ]