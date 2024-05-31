from django.core.management.base import BaseCommand

from apps.talent.models import Person, BountyClaim


class Command(BaseCommand):
    help = "Calculate Person points based on completed bounty claims"

    def handle(self, *args, **options):
        updated_count = 0

        for person in Person.objects.all():
            points = 0
            bounty_claims = BountyClaim.objects.filter(person=person)
            for bounty_claim in bounty_claims:
                if bounty_claim.status == bounty_claim.Status.COMPLETED:
                    points += bounty_claim.bounty.points
            person.points = points
            person.save()
            updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Updated points of {updated_count} person objects."))
