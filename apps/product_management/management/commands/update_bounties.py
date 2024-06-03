from django.core.management.base import BaseCommand

from apps.product_management.models import Bounty
from apps.talent.models import BountyClaim


class Command(BaseCommand):
    help = "Update bounties"

    def handle(self, *args, **options):
        updated_count = 0
        for bounty in Bounty.objects.all():
            last_claim = (
                bounty.bountyclaim_set.filter(
                    status__in=[
                        BountyClaim.Status.GRANTED,
                        BountyClaim.Status.COMPLETED,
                        BountyClaim.Status.CONTRIBUTED,
                    ]
                )
                .select_related("person", "bounty")
                .first()
            )
            if last_claim:
                bounty.claimed_by = last_claim.person
                bounty.save()
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Updated {updated_count} bounties."))
