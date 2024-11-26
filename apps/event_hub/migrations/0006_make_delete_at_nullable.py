from django.db import migrations, models
from django.db.utils import ProgrammingError

def check_and_create_field(apps, schema_editor):
    # Get the database connection
    connection = schema_editor.connection
    
    with connection.cursor() as cursor:
        # Check if column exists using information_schema
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'event_hub_eventlog' 
            AND column_name = 'delete_at';
        """)
        
        if not cursor.fetchone():
            # Column doesn't exist, so add it
            cursor.execute(
                "ALTER TABLE event_hub_eventlog ADD COLUMN delete_at timestamp with time zone NULL"
            )

class Migration(migrations.Migration):
    dependencies = [
        ('event_hub', '0005_auto_20241126_1713'),
    ]

    operations = [
        migrations.RunPython(check_and_create_field, migrations.RunPython.noop),
    ]