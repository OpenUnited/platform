from django.db import migrations, models
from django.db.utils import ProgrammingError

def check_field_exists(apps, schema_editor):
    # Get the database connection
    db_alias = schema_editor.connection.alias
    try:
        # Try to query the field
        schema_editor.execute("SELECT parent_event_id FROM event_hub_eventlog LIMIT 1")
        # If we get here, the field exists
        return True
    except ProgrammingError:
        # If we get here, the field doesn't exist
        return False

def add_field_if_not_exists(apps, schema_editor):
    if not check_field_exists(apps, schema_editor):
        # Only add the field if it doesn't exist
        migrations.AddField(
            model_name='eventlog',
            name='parent_event_id',
            field=models.IntegerField(null=True),
        ).database_forwards('event_hub', schema_editor, None, None)

class Migration(migrations.Migration):
    dependencies = [
        ('event_hub', '0004_remove_eventlog_processed_and_more'),
    ]

    operations = [
        migrations.RunPython(add_field_if_not_exists, migrations.RunPython.noop),
    ]