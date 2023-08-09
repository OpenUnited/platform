import logging
import datetime
from django.db import transaction
from django.db.models import Sum

from commerce.utils import (
    CurrencyTypes,
    PaymentTypes,
    PaymentStatusOptions,
    LifecycleStatusOptions,
)
from .models import (
    Organisation,
    OrganisationAccount,
    OrganisationAccountCredit,
    OrganisationAccountCreditReasons,
    PointTypes,
    Cart,
    PointPriceConfiguration,
    SalesOrder,
    InboundPayment,
)


logger = logging.getLogger(__name__)


class OrganisationService:
    @staticmethod
    def create(**kwargs):
        organisation = Organisation(**kwargs)
        organisation.save()

        return organisation

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
    def create(**kwargs):
        organisation_account = OrganisationAccount(**kwargs)
        organisation_account.save()

        return organisation_account

    # @transaction.atomic
    # def create(
    #     self,
    #     organisation: Organisation,
    #     liquid_points_balance: int,
    #     nonliquid_points_balance: int,
    # ) -> OrganisationAccount:
    #     organisation_account = OrganisationAccount(
    #         organisation=organisation,
    #         liquid_points_balance=liquid_points_balance,
    #         nonliquid_points_balance=nonliquid_points_balance,
    #     )
    #     organisation_account.save()
    #     return organisation_account

    @transaction.atomic
    def update(
        self,
        id: int,
        organisation: Organisation,
        liquid_points_balance: int,
        nonliquid_points_balance: int,
    ):
        try:
            organisation_account = OrganisationAccount.objects.get(pk=id)
            organisation_account.organisation = organisation
            organisation_account.liquid_points_balance = liquid_points_balance
            organisation_account.nonliquid_points_balance = nonliquid_points_balance
            organisation_account.save()
            return organisation_account
        except OrganisationAccount.DoesNotExist as e:
            logger.error(f"Failed to update OrganisationAccount due to: {e}")

    @transaction.atomic
    def delete(self, id: int) -> bool:
        try:
            organisation_account = OrganisationAccount.objects.get(pk=id)
            organisation_account.delete()

            return True
        except OrganisationAccount.DoesNotExist as e:
            logger.error(f"Failed to delete OrganisationAccount due to: {e}")
            return False

    @staticmethod
    def credit(account: OrganisationAccount, granting_object: object) -> None:
        credit_reason = OrganisationAccountCreditReasons.GRANT
        type_of_points = PointTypes.NONLIQUID

        if (granting_object.__class__.__name__.lower()) == "salesorder":
            credit_reason = OrganisationAccountCreditReasons.SALE
            type_of_points = PointTypes.LIQUID

        # only grant points if granting_object has no existing related credit
        if not granting_object.organisation_account_credit:
            organisation_account_credit_service = OrganisationAccountCreditService()
            credit = organisation_account_credit_service.create(
                organisation_account=account,
                number_of_points=granting_object.number_of_points,
                credit_reason=credit_reason,
                type_of_points=type_of_points,
            )
            OrganisationAccountService._recalculate_balances(account)
            granting_object.mark_points_as_granted(credit)

    @staticmethod
    def _recalculate_balances(account: OrganisationAccount) -> None:
        nonliquid_credits = (
            OrganisationAccountCredit.objects.filter(
                organisation_account=account, type_of_points=PointTypes.NONLIQUID
            ).aggregate(Sum("number_of_points"))["number_of_points__sum"]
            or 0
        )
        nonliquid_debits = 0
        account.nonliquid_points_balance = nonliquid_credits - nonliquid_debits

        liquid_credits = (
            OrganisationAccountCredit.objects.filter(
                organisation_account=account, type_of_points=PointTypes.LIQUID
            ).aggregate(Sum("number_of_points"))["number_of_points__sum"]
            or 0
        )
        liquid_debits = 0
        account.liquid_points_balance = liquid_credits - liquid_debits

        account.save()


class OrganisationAccountCreditService:
    @staticmethod
    def create(**kwargs):
        org_acc_credit = OrganisationAccountCredit(**kwargs)
        org_acc_credit.save()

        return org_acc_credit

    # @transaction.atomic
    # def create(
    #     self, organisation_account: OrganisationAccount, number_of_points: int
    # ) -> OrganisationAccountCredit:
    #     org_acc_credit = OrganisationAccountCredit(
    #         organisation_account=organisation_account, number_of_points=number_of_points
    #     )
    #     org_acc_credit.save()
    #     return org_acc_credit

    @transaction.atomic
    def update(
        self,
        id: int,
        organisation_account: OrganisationAccount,
        number_of_points: int,
        type_of_points: PointTypes,
        credit_reason: OrganisationAccountCreditReasons,
    ) -> OrganisationAccountCredit:
        org_acc_credit = OrganisationAccountCredit.objects.get(pk=id)
        org_acc_credit.organisation_account = organisation_account
        org_acc_credit.number_of_points = number_of_points
        org_acc_credit.type_of_points = type_of_points
        org_acc_credit.credit_reason = credit_reason
        org_acc_credit.save()

    @transaction.atomic
    def delete(self, id: int) -> bool:
        try:
            org_acc_credit = OrganisationAccountCredit.objects.get(pk=id)
            org_acc_credit.delete()
        except OrganisationAccountCredit.DoesNotExist as e:
            logger.error(f"Failed to delete OrganisationAccountCredit due to: {e}")
            return False


class CartService:
    @staticmethod
    def create(**kwargs):
        currency_of_payment = kwargs.get("current_of_payment", None)
        if not currency_of_payment:
            currency_of_payment = Cart.currency_of_payment.field.default

        price_per_point_in_cents = CartService._get_point_inbound_price_in_cents(
            currency_of_payment
        )

        number_of_points = kwargs.get("number_of_points", None)
        if not number_of_points:
            number_of_points = Cart.number_of_points.field.default

        subtotal_in_cents = number_of_points * price_per_point_in_cents
        sales_tax_in_cents = 0  # TODO: create logic for sales tax based on org account
        total_payable_in_cents = subtotal_in_cents + sales_tax_in_cents

        kwargs["subtotal_in_cents"] = subtotal_in_cents
        kwargs["sales_tax_in_cents"] = sales_tax_in_cents
        kwargs["total_payable_in_cents"] = total_payable_in_cents
        kwargs["price_per_point_in_cents"] = price_per_point_in_cents

        cart = Cart(**kwargs)
        cart.save()

        return cart

    # @transaction.atomic
    # def create(
    #     self,
    #     organisation_account: OrganisationAccount,
    #     creator: Person,
    #     number_of_points: int,
    #     currency_of_payment: CurrencyTypes,
    #     payment_type: PaymentTypes,
    # ) -> Cart:
    #     price_per_point_in_cents = self._get_point_inbound_price_in_cents(
    #         currency_of_payment
    #     )
    #     subtotal_in_cents = number_of_points * price_per_point_in_cents
    #     sales_tax_in_cents = 0  # TODO: create logic for sales tax based on org account
    #     total_payable_in_cents = subtotal_in_cents + sales_tax_in_cents

    #     cart = Cart(
    #         organisation_account=organisation_account,
    #         creator=creator,
    #         number_of_points=number_of_points,
    #         currency_of_payment=currency_of_payment,
    #         payment_type=payment_type,
    #         price_per_point_in_cents=price_per_point_in_cents,
    #         subtotal_in_cents=subtotal_in_cents,
    #         sales_tax_in_cents=sales_tax_in_cents,
    #         total_payable_in_cents=total_payable_in_cents,
    #     )
    #     cart.save()

    #     return cart

    @transaction.atomic
    def delete(self, id: int) -> bool:
        try:
            cart = Cart.objects.get(pk=id)
            cart.delete()
            return True
        except Cart.DoesNotExist as e:
            logger.error(f"Failed to delete OrganisationAccountCredit due to: {e}")
            return False

    @staticmethod
    def _get_point_inbound_price_in_cents(currency: CurrencyTypes) -> int:
        conversion_rate_queryset = PointPriceConfiguration.objects.filter(
            applicable_from_date__lte=datetime.date.today()
        ).order_by("-created_at")
        conversion_rates = conversion_rate_queryset.first()

        if currency == CurrencyTypes.USD:
            return conversion_rates.usd_point_inbound_price_in_cents
        elif currency == CurrencyTypes.EUR:
            return conversion_rates.eur_point_inbound_price_in_cents
        elif currency == CurrencyTypes.GBP:
            return conversion_rates.gbp_point_inbound_price_in_cents
        else:
            raise ValueError("No conversion rate for given currency.", currency)


class SalesOrderService:
    @transaction.atomic
    def create(
        self,
        organisation_account: OrganisationAccount,
        organisation_account_credit: OrganisationAccountCredit,
        cart: Cart,
        number_of_points: int,
        currency_of_payments: CurrencyTypes,
        price_per_point_in_cents: int,
        subtotal_in_cents: int,
        sales_tax_in_cents: int,
        total_payable_in_cents: int,
        payment_type: PaymentTypes,
        payment_status: PaymentStatusOptions,
        process_status: LifecycleStatusOptions,
    ) -> SalesOrder:
        sales_order = SalesOrder(
            organisation_account=organisation_account,
            organisation_account_credit=organisation_account_credit,
            cart=cart,
            number_of_points=number_of_points,
            currency_of_payments=currency_of_payments,
            price_per_point_in_cents=price_per_point_in_cents,
            subtotal_in_cents=subtotal_in_cents,
            sales_tax_in_cents=sales_tax_in_cents,
            total_payable_in_cents=total_payable_in_cents,
            payment_type=payment_type,
            payment_status=payment_status,
            process_status=process_status,
        )
        sales_order.save()

        return sales_order

    @transaction.atomic
    def update(
        self,
        id: int,
        organisation_account: OrganisationAccount,
        organisation_account_credit: OrganisationAccountCredit,
        cart: Cart,
        number_of_points: int,
        currency_of_payments: CurrencyTypes,
        price_per_point_in_cents: int,
        subtotal_in_cents: int,
        sales_tax_in_cents: int,
        total_payable_in_cents: int,
        payment_type: PaymentTypes,
        payment_status: PaymentStatusOptions,
        process_status: LifecycleStatusOptions,
    ) -> SalesOrder:
        try:
            sales_order = SalesOrder.objects.get(pk=id)
            sales_order.organisation_account = organisation_account
            sales_order.organisation_account_credit = organisation_account_credit
            sales_order.cart = cart
            sales_order.number_of_points = number_of_points
            sales_order.currency_of_payments = currency_of_payments
            sales_order.price_per_point_in_cents = price_per_point_in_cents
            sales_order.subtotal_in_cents = subtotal_in_cents
            sales_order.sales_tax_in_cents = sales_tax_in_cents
            sales_order.total_payable_in_cents = total_payable_in_cents
            sales_order.payment_type = payment_type
            sales_order.payment_status = payment_status
            sales_order.process_status = process_status

            sales_order.save()

            return sales_order
        except SalesOrder.DoesNotExist as e:
            logger.error(f"Failed to update SalesOrder due to: {e}")
            return None

    @transaction.atomic
    def create_from_cart(self, cart: Cart) -> SalesOrder:
        sales_order = SalesOrder(
            organisation_account=cart.organisation_account,
            cart=cart,
            number_of_points=cart.number_of_points,
            currency_of_payment=cart.currency_of_payment,
            price_per_point_in_cents=cart.price_per_point_in_cents,
            subtotal_in_cents=cart.subtotal_in_cents,
            payment_type=cart.payment_type,
            sales_tax_in_cents=cart.sales_tax_in_cents,
            total_payable_in_cents=cart.total_payable_in_cents,
        )
        sales_order.save()

        return sales_order

    @transaction.atomic
    def delete(self, id: int) -> bool:
        try:
            sales_order = SalesOrder.objects.get(pk=id)
            sales_order.delete()
        except SalesOrder.DoesNotExist as e:
            logger.error(f"Failed to delete SalesOrder due to: {e}")

    def register_payment(
        self,
        sales_order: SalesOrder,
        currency_of_payment: CurrencyTypes,
        amount_paid_in_cents: int,
        detail: str,
    ):
        payment = InboundPayment.objects.create(
            sales_order=sales_order,
            payment_type=sales_order.payment_type,
            currency_of_payment=currency_of_payment,
            amount_paid_in_cents=amount_paid_in_cents,
            transaction_detail=detail,
        )
        if self._is_paid_in_full(sales_order, currency_of_payment):
            sales_order.payment_status = PaymentStatusOptions.PAID
            sales_order.save
            # credit points to organisation account
            OrganisationAccountService.credit(self)

        return payment

    def _is_paid_in_full(
        self, sales_order: SalesOrder, currency_of_payment: CurrencyTypes
    ) -> bool:
        total_paid_in_cents = InboundPayment.objects.filter(
            sales_order=sales_order, currency_of_payment=currency_of_payment
        ).aggregate(Sum("amount_paid_in_cents"))["amount_paid_in_cents__sum"]
        if total_paid_in_cents == self.total_payable_in_cents:
            return True
        else:
            return False

    @staticmethod
    def mark_points_as_granted(sales_order, credit):
        sales_order.organisation_account_credit = credit
        sales_order.process_status = LifecycleStatusOptions.COMPLETE
        sales_order.save()


class PointPriceConfigurationService:
    @transaction.atomic
    def create(
        self,
        applicable_from_date: datetime.date,
        usd_point_inbound_price_in_cents: int,
        eur_point_inbound_price_in_cents: int,
        gbp_point_inbound_price_in_cents: int,
        usd_point_outbound_price_in_cents: int,
        eur_point_outbound_price_in_cents: int,
        gbp_point_outbound_price_in_cents: int,
    ) -> PointPriceConfiguration:
        if not self._is_profitable(
            usd_point_inbound_price_in_cents,
            usd_point_outbound_price_in_cents,
            eur_point_inbound_price_in_cents,
            eur_point_outbound_price_in_cents,
            gbp_point_inbound_price_in_cents,
            gbp_point_outbound_price_in_cents,
        ):
            logger.error(
                f"A non-profitable PointPriceConfiguration is tried to be created. No configuration is created."
            )
            return None

        point_price_config = PointPriceConfiguration(
            applicable_from_date=applicable_from_date,
            usd_point_inbound_price_in_cents=usd_point_inbound_price_in_cents,
            eur_point_inbound_price_in_cents=eur_point_inbound_price_in_cents,
            gbp_point_inbound_price_in_cents=gbp_point_inbound_price_in_cents,
            usd_point_outbound_price_in_cents=usd_point_outbound_price_in_cents,
            eur_point_outbound_price_in_cents=eur_point_outbound_price_in_cents,
            gbp_point_outbound_price_in_cents=gbp_point_outbound_price_in_cents,
        )
        point_price_config.save()
        return point_price_config

    @transaction.atomic
    def update(
        self,
        id: int,
        applicable_from_date: datetime.date = None,
        usd_point_inbound_price_in_cents: int = None,
        eur_point_inbound_price_in_cents: int = None,
        gbp_point_inbound_price_in_cents: int = None,
        usd_point_outbound_price_in_cents: int = None,
        eur_point_outbound_price_in_cents: int = None,
        gbp_point_outbound_price_in_cents: int = None,
    ) -> PointPriceConfiguration:
        try:
            point_price_config = self.get(id)
        except PointPriceConfiguration.DoesNotExist as e:
            logger.error(f"Failed to update SalesOrder due to: {e}")
            return None

        if not self._is_profitable(
            usd_point_inbound_price_in_cents,
            usd_point_outbound_price_in_cents,
            eur_point_inbound_price_in_cents,
            eur_point_outbound_price_in_cents,
            gbp_point_inbound_price_in_cents,
            gbp_point_outbound_price_in_cents,
        ):
            logger.error(
                f"A non-profitable PointPriceConfiguration is tried to be updated. No configuration is updated."
            )
            return None

        if applicable_from_date is not None:
            point_price_config.applicable_from_date = applicable_from_date
        if usd_point_inbound_price_in_cents is not None:
            point_price_config.usd_point_inbound_price_in_cents = (
                usd_point_inbound_price_in_cents
            )
        if eur_point_inbound_price_in_cents is not None:
            point_price_config.eur_point_inbound_price_in_cents = (
                eur_point_inbound_price_in_cents
            )
        if gbp_point_inbound_price_in_cents is not None:
            point_price_config.gbp_point_inbound_price_in_cents = (
                gbp_point_inbound_price_in_cents
            )
        if usd_point_outbound_price_in_cents is not None:
            point_price_config.usd_point_outbound_price_in_cents = (
                usd_point_outbound_price_in_cents
            )
        if eur_point_outbound_price_in_cents is not None:
            point_price_config.eur_point_outbound_price_in_cents = (
                eur_point_outbound_price_in_cents
            )
        if gbp_point_outbound_price_in_cents is not None:
            point_price_config.gbp_point_outbound_price_in_cents = (
                gbp_point_outbound_price_in_cents
            )

        point_price_config.save()
        return point_price_config

    def _is_profitable(
        self,
        usd_point_inbound_price_in_cents,
        usd_point_outbound_price_in_cents,
        eur_point_inbound_price_in_cents,
        eur_point_outbound_price_in_cents,
        gbp_point_inbound_price_in_cents,
        gbp_point_outbound_price_in_cents,
    ):
        profitable = True
        if usd_point_inbound_price_in_cents < usd_point_outbound_price_in_cents:
            profitable = False

        if eur_point_inbound_price_in_cents < eur_point_outbound_price_in_cents:
            profitable = False

        if gbp_point_inbound_price_in_cents < gbp_point_outbound_price_in_cents:
            profitable = False

        return profitable

    @transaction.atomic
    def delete(self, id):
        point_price_config = self.get(id)
        if point_price_config is not None:
            point_price_config.delete()
            return True
        return False
