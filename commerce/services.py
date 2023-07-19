import logging
from django.db import transaction
from django.db.models import Sum

from .models import Organisation, OrganisationAccount, OrganisationAccountCredit, OrganisationAccountCreditReasons, PointTypes


logger = logging.getLogger(__name__)


class OrganisationService:
    def __init__(self):
        pass

    @transaction.atomic
    def create(self, name: str) -> Organisation:
        try:
            organisation = Organisation(name=name)
            organisation.save()
            return organisation
        except Exception as e:
            logger.error(f"Failed to create OrganisationPerson due to: {e}")
            return None

    @transaction.atomic
    def update(self, id: int, name: str) -> Organisation:
        try:
            organisation = Organisation.objects.get(pk=id)
            organisation.name = name
            organisation.save()
            return organisation
        except Organisation.DoesNotExist as e:
            logger.error(f"Failed to update Organisation due to: {e}")
            return None

    @transaction.atomic
    def delete(self, id: int) -> bool:
        try:
            organisation = Organisation.objects.get(pk=id)
            organisation.delete()
            return True
        except Organisation.DoesNotExist as e:
            logger.error(f"Failed to delete Organisation due to: {e}")
            return False


class OrganisationAccountService:
    @staticmethod
    def credit(account: OrganisationAccount, granting_object: object) -> None:
        credit_reason = OrganisationAccountCreditReasons.GRANT
        type_of_points = PointTypes.NONLIQUID

        if(granting_object.__class__.__name__.lower()) == "salesorder":
            credit_reason = OrganisationAccountCreditReasons.SALE
            type_of_points = PointTypes.LIQUID

        # only grant points if granting_object has no existing related credit
        if not granting_object.organisation_account_credit:
            credit = OrganisationAccountCredit.objects.create(
                organisation_account=account,
                number_of_points=granting_object.number_of_points,
                credit_reason=credit_reason,
                type_of_points=type_of_points,
            )
            OrganisationAccountService._recalculate_balances(account)
            granting_object.mark_points_as_granted(credit)

    @staticmethod
    def _recalculate_balances(account: OrganisationAccount) -> None:
        nonliquid_credits = OrganisationAccountCredit.objects.filter(organisation_account=account, type_of_points=PointTypes.NONLIQUID).aggregate(Sum('number_of_points'))['number_of_points__sum'] or 0
        nonliquid_debits = 0
        account.nonliquid_points_balance = nonliquid_credits - nonliquid_debits

        liquid_credits = OrganisationAccountCredit.objects.filter(organisation_account=account, type_of_points=PointTypes.LIQUID).aggregate(Sum('number_of_points'))['number_of_points__sum'] or 0
        liquid_debits = 0
        account.liquid_points_balance = liquid_credits - liquid_debits

        account.save()
