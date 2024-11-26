from django.db import migrations, models
from django.db.utils import ProgrammingError

def check_and_create_field(apps, schema_editor):
    # Get the database connection
    connection = schema_editor.connection
    
    # Check if field exists
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT parent_event_id FROM event_hub_eventlog LIMIT 1")
    except ProgrammingError:
        # Field doesn't exist, so add it
        with connection.cursor() as cursor:
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