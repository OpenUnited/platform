# Generated by Django 4.2.2 on 2024-11-10 18:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('talent', '0014_delete_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bountyclaim',
            name='status',
            field=models.CharField(choices=[('Requested', 'Requested'), ('Cancelled', 'Cancelled'), ('Rejected', 'Rejected'), ('Granted', 'Granted'), ('Contributed', 'Contributed'), ('Completed', 'Completed'), ('Failed', 'Failed')], default='Requested', max_length=20),
        ),
    ]