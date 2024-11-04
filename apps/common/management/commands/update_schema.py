"""
Management command to update the platform schema documentation.
"""

from django.core.management.base import BaseCommand
from apps.common.schema import save_schema


class Command(BaseCommand):
    help = 'Updates the platform schema documentation'

    def handle(self, *args, **options):
        try:
            save_schema()
            self.stdout.write(
                self.style.SUCCESS('Successfully updated schema documentation')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to update schema: {str(e)}')
            )
