from django.db import migrations, models
from django.db.utils import ProgrammingError

def make_delete_at_nullable(apps, schema_editor):
    # Get the database connection
    connection = schema_editor.connection
    
    with connection.cursor() as cursor:
        # Alter column to allow NULL
        cursor.execute(
            "ALTER TABLE event_hub_eventlog ALTER COLUMN delete_at DROP NOT NULL"
        )

class Migration(migrations.Migration):
    dependencies = [
        ('event_hub', '0006_make_delete_at_nullable'),
    ]

    operations = [
        migrations.RunPython(make_delete_at_nullable, migrations.RunPython.noop),
    ]
