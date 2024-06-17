from django.core.management.base import BaseCommand

from apps.security.models import ProductRoleAssignment


class Command(BaseCommand):
    help = "Update product roles from int to string values"

    def handle(self, *args, **options):
        updated_count = 0
        product_role_mapping = {
            "0": "Contributor",
            "1": "Manager",
            "2": "Admin",
        }

        for product_role in ProductRoleAssignment.objects.all():
            if len(product_role.role) == 1:
                product_role.role = product_role_mapping[product_role.role]
                product_role.save()
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Updated {updated_count} product roles."))
