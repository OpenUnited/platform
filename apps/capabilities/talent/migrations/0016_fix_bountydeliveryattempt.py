from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('talent', '0015_alter_bountyclaim_status'),
    ]

    operations = [
        # First make the field nullable to handle any existing NULL values
        migrations.AlterField(
            model_name='bountydeliveryattempt',
            name='delivery_message',
            field=models.TextField(null=True, blank=True, max_length=2000),
        ),
        # Then update any NULL values to empty string
        migrations.RunSQL(
            "UPDATE talent_bountydeliveryattempt SET delivery_message = '' WHERE delivery_message IS NULL",
            reverse_sql="UPDATE talent_bountydeliveryattempt SET delivery_message = NULL WHERE delivery_message = ''",
        ),
        # Finally make it non-nullable with default empty string
        migrations.AlterField(
            model_name='bountydeliveryattempt',
            name='delivery_message',
            field=models.TextField(blank=True, default='', max_length=2000),
        ),
        # Update PersonSkill separately
        migrations.AlterField(
            model_name='personskill',
            name='expertise',
            field=models.ManyToManyField(blank=True, to='talent.expertise'),
        ),
    ] 