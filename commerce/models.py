from openunited.mixins import TimeStampMixin, UUIDMixin
from django.db import models
from django.db.models import Sum
from .utils import *
import datetime
import uuid

from django.db.models.signals import post_save
from django.core.validators import RegexValidator
from django.dispatch import receiver
from model_utils import FieldTracker
from notifications.signals import notify

import engagement.tasks
from openunited.mixins import TimeStampMixin, UUIDMixin
from engagement.models import Notification
from talent.models import Person
from product_management.models import Bounty

class Organisation(TimeStampMixin):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    username = models.CharField(max_length=39,
                                unique=True,
                                default='',
                                validators=[
                                    RegexValidator(
                                        regex="^[a-z0-9]*$",
                                        message="Username may only contain letters and numbers",
                                        code="invalid_username"
                                    )
                                ])
    name = models.CharField(max_length=512, unique=True)
    photo = models.ImageField(upload_to='avatars/', null=True, blank=True)

    class Meta:
        verbose_name_plural = "Organisations"

    def get_username(self):
        return self.username

    def __str__(self):
        return self.name
        
class OrganisationAccountCredit(TimeStampMixin, UUIDMixin):
    organisation_account = models.ForeignKey(to='OrganisationAccount', on_delete=models.CASCADE)
    number_of_points = models.PositiveIntegerField()
    type_of_points = models.IntegerField(choices=PointTypes.choices(), default=PointTypes.NONLIQUID)
    credit_reason = models.IntegerField(choices=OrganisationAccountCreditReasons.choices(), default=OrganisationAccountCreditReasons.GRANT)


class OrganisationAccount(models.Model):
    organisation = models.ForeignKey(to="Organisation", on_delete=models.CASCADE)
    liquid_points_balance = models.PositiveBigIntegerField()
    nonliquid_points_balance = models.PositiveBigIntegerField()

    def credit(self, granting_object):
        credit_reason = OrganisationAccountCreditReasons.GRANT
        type_of_points = PointTypes.NONLIQUID
        if(granting_object.__class__.__name__.lower()) == "salesorder":
            credit_reason = OrganisationAccountCreditReasons.SALE
            type_of_points = PointTypes.LIQUID

        #only grant points if granting_object has no existing related credit
        if not granting_object.organisation_account_credit:
            credit = OrganisationAccountCredit.objects.create(
                        organisation_account = self,
                        number_of_points = granting_object.number_of_points,
                        credit_reason = credit_reason,
                        type_of_points = type_of_points,
                    )
            self.recalculate_balances()
            granting_object.mark_points_as_granted(credit)

    def recalculate_balances(self):
        nonliquid_credits = OrganisationAccountCredit.objects.filter(organisation_account=self, type_of_points=PointTypes.NONLIQUID).aggregate(Sum('number_of_points'))['number_of_points__sum'] or 0
        nonliquid_debits = 0
        self.nonliquid_points_balance = nonliquid_credits - nonliquid_debits

        liquid_credits = OrganisationAccountCredit.objects.filter(organisation_account=self, type_of_points=PointTypes.LIQUID).aggregate(Sum('number_of_points'))['number_of_points__sum'] or 0
        liquid_debits = 0
        self.liquid_points_balance = liquid_credits - liquid_debits

        self.save()


class Cart(TimeStampMixin, UUIDMixin):
    organisation_account = models.ForeignKey(OrganisationAccount, on_delete=models.CASCADE)
    creator = models.ForeignKey(to="talent.Person", on_delete=models.CASCADE)
    number_of_points = models.IntegerField(default=500)
    currency_of_payment = models.IntegerField(choices=CurrencyTypes.choices(), default=CurrencyTypes.USD)
    price_per_point_in_cents = models.IntegerField()
    subtotal_in_cents = models.PositiveBigIntegerField()
    sales_tax_in_cents = models.PositiveBigIntegerField()
    total_payable_in_cents = models.PositiveBigIntegerField()
    payment_type = models.IntegerField(choices=PaymentTypes.choices(), default=PaymentTypes.ONLINE)

    @staticmethod
    def new(organisation_account, creator, number_of_points, currency_of_payment, payment_type):  
        price_per_point_in_cents = PointPriceConfiguration.get_point_inbound_price_in_cents(currency_of_payment)
        subtotal_in_cents = number_of_points * price_per_point_in_cents
        sales_tax_in_cents = 0 #TODO: create logic for sales tax based on org account
        total_payable_in_cents = subtotal_in_cents + sales_tax_in_cents

        cart = Cart.objects.create(
            organisation_account = organisation_account,
            creator = creator,
            number_of_points = number_of_points,
            currency_of_payment = currency_of_payment,
            payment_type = payment_type,
            price_per_point_in_cents = price_per_point_in_cents,
            subtotal_in_cents = subtotal_in_cents,
            sales_tax_in_cents = sales_tax_in_cents, 
            total_payable_in_cents = total_payable_in_cents
        )

        return cart


class Grant(models.Model):
    organisation_account = models.ForeignKey(OrganisationAccount, on_delete=models.CASCADE)
    nominating_bee_keeper = models.ForeignKey(to="talent.Person", on_delete=models.CASCADE, related_name='nominator')
    approving_bee_keeper = models.ForeignKey(to="talent.Person", on_delete=models.CASCADE, related_name='approver')
    description = models.TextField(max_length=1024)
    number_of_points = models.IntegerField(default=500)
    status = models.IntegerField(choices=LifecycleStatusOptions.choices(), default=LifecycleStatusOptions.NEW)
    organisation_account_credit = models.ForeignKey(to="OrganisationAccountCredit", on_delete=models.CASCADE, null=True)

    def mark_points_as_granted(self, credit):
            self.organisation_account_credit = credit
            self.status = LifecycleStatusOptions.COMPLETE
            self.save()


class SalesOrder(TimeStampMixin, UUIDMixin):
    organisation_account = models.ForeignKey(OrganisationAccount, on_delete=models.CASCADE)
    organisation_account_credit = models.ForeignKey(to="OrganisationAccountCredit", on_delete=models.CASCADE, null=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    number_of_points = models.IntegerField()
    currency_of_payment = models.IntegerField(choices=CurrencyTypes.choices(), default=CurrencyTypes.USD)
    price_per_point_in_cents = models.IntegerField()
    subtotal_in_cents = models.PositiveBigIntegerField()
    sales_tax_in_cents = models.PositiveBigIntegerField()
    total_payable_in_cents = models.PositiveBigIntegerField()
    payment_type = models.IntegerField(choices=PaymentTypes.choices(), default=PaymentTypes.ONLINE)
    payment_status = models.IntegerField(choices=PaymentStatusOptions.choices(), default=PaymentStatusOptions.PENDING)
    process_status = models.IntegerField(choices=LifecycleStatusOptions.choices(), default=LifecycleStatusOptions.NEW)

    @staticmethod
    def create_from_cart(cart):
        sales_order = SalesOrder.objects.create(
            organisation_account = cart.organisation_account,
            cart = cart,
            number_of_points = cart.number_of_points,
            currency_of_payment = cart.currency_of_payment,
            price_per_point_in_cents = cart.price_per_point_in_cents,
            subtotal_in_cents = cart.subtotal_in_cents,
            payment_type = cart.payment_type,
            sales_tax_in_cents = cart.sales_tax_in_cents, 
            total_payable_in_cents = cart.total_payable_in_cents,
        )
        return sales_order

    def register_payment(self, currency_of_payment, amount_paid_in_cents, detail):
        payment = InboundPayment.objects.create(
            sales_order = self,
            payment_type = self.payment_type,
            currency_of_payment = currency_of_payment,
            amount_paid_in_cents = amount_paid_in_cents,
            transaction_detail = detail
        )
        if self.is_paid_in_full():
            self.payment_status = PaymentStatusOptions.PAID
            self.save
            #credit points to organisation account
            self.organisation_account.credit(self)
            
        return payment


    def is_paid_in_full(self):
        total_paid_in_cents = InboundPayment.objects.filter(sales_order=self, currency_of_payment=self.currency_of_payment).aggregate(Sum('amount_paid_in_cents'))['amount_paid_in_cents__sum']
        if total_paid_in_cents == self.total_payable_in_cents:
            return True
        else:
            return False

    def mark_points_as_granted(self, credit):
            self.organisation_account_credit = credit
            self.process_status = LifecycleStatusOptions.COMPLETE
            self.save()


class InboundPayment(TimeStampMixin, UUIDMixin):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE)
    payment_type = models.IntegerField(choices=PaymentTypes.choices(), default=PaymentTypes.ONLINE)
    currency_of_payment = models.IntegerField(choices=CurrencyTypes.choices(), default=CurrencyTypes.USD)
    amount_paid_in_cents = models.PositiveBigIntegerField()
    transaction_detail = models.TextField(max_length=1024)


class OrganisationAccountDebit(TimeStampMixin, UUIDMixin):
    DebitReason = (
        (1, "TRANSFER"),
        (2, "EXPIRY"),
    )
    organisation_account = models.ForeignKey(to='OrganisationAccount', on_delete=models.CASCADE)
    number_of_points = models.PositiveIntegerField
    type_of_points = models.IntegerField(choices=PointTypes.choices(), default=PointTypes.NONLIQUID)
    debit_reason = models.IntegerField(choices=DebitReason, default=0)


class ProductAccount(models.Model):
    product = models.ForeignKey(to="product_management.Product", on_delete=models.CASCADE)
    liquid_points_balance = models.PositiveBigIntegerField()
    nonliquid_points_balance = models.PositiveBigIntegerField()


class ProductAccountCredit(TimeStampMixin, UUIDMixin):
    #each product account credit has a matching organisation account debit
    organisation_account_debit = models.ForeignKey(OrganisationAccountDebit, on_delete=models.CASCADE)
    product_account = models.ForeignKey(ProductAccount, on_delete=models.CASCADE)
    number_of_points = models.PositiveIntegerField()
    type_of_points = models.IntegerField(choices=PointTypes.choices(), default=PointTypes.NONLIQUID)
    actioned_by = models.ForeignKey(to="talent.Person", on_delete=models.CASCADE)
    

class ProductAccountReservation(TimeStampMixin, UUIDMixin):
    bounty_claim = models.ForeignKey(to="talent.BountyClaim", on_delete=models.CASCADE)
    number_of_points = models.PositiveIntegerField()
    type_of_points = models.IntegerField(choices=PointTypes.choices(), default=PointTypes.NONLIQUID)
    

class ProductAccountDebit(TimeStampMixin, UUIDMixin):
    bounty_claim = models.ForeignKey(to="talent.BountyClaim", on_delete=models.CASCADE)
    number_of_points = models.PositiveIntegerField()
    type_of_points = models.IntegerField(choices=PointTypes.choices(), default=PointTypes.NONLIQUID)


class ContributorAccount(models.Model):
    owner = models.ForeignKey(to="talent.Person", on_delete=models.CASCADE)
    community_status = models.IntegerField(choices=CommunityStatusOptions.choices(), default=CommunityStatusOptions.DRONE)
    liquid_points_balance = models.PositiveBigIntegerField(default=0)
    nonliquid_points_balance = models.PositiveBigIntegerField(default=0)
    

class PaymentOrder(TimeStampMixin, UUIDMixin):
    contributor_account = models.ForeignKey(ContributorAccount, on_delete=models.CASCADE)
    currency_of_payment = models.IntegerField(choices=CurrencyTypes.choices(), default=CurrencyTypes.USD)
    subtotal_in_cents = models.PositiveBigIntegerField()
    sales_tax_in_cents = models.PositiveBigIntegerField()
    total_payable_in_cents = models.PositiveBigIntegerField()
    PaymentType = (
        (1, "PARTNER"),
        (2, "BANK TRANSFER"),
    )
    payment_type = models.IntegerField(choices=PaymentType, default=0)
    status = models.IntegerField(choices=LifecycleStatusOptions.choices(), default=LifecycleStatusOptions.NEW)


class OutboundPayment(TimeStampMixin, UUIDMixin):
    payment_order = models.ForeignKey(PaymentOrder, on_delete=models.CASCADE)
    details = models.TextField(max_length=1024)


class ContributorReward(TimeStampMixin, UUIDMixin):
    RewardedActions = (
        (1, "INVITED FRIENDS"),
        (2, "VERIFIED IDENTITY"),
    )
    contributor_account = models.ForeignKey(ContributorAccount, on_delete=models.CASCADE)
    action = models.IntegerField(choices=RewardedActions, default=0)
    points = models.IntegerField(default=10)


class ContributorAccountCredit(TimeStampMixin, UUIDMixin):
    CreditReason = (
        (1, "BOUNTY"),
        (2, "LIQUIDATION"),
        (3, "REWARD")
    )
    reason = models.IntegerField(choices=CreditReason, default=0)
    bounty_claim = models.ForeignKey(to="talent.BountyClaim", on_delete=models.CASCADE)
    contributor_account = models.ForeignKey(ContributorAccount, on_delete=models.CASCADE)
    number_of_points = models.PositiveIntegerField()
    type_of_points = models.IntegerField(choices=PointTypes.choices(), default=PointTypes.NONLIQUID)
    #when liquid points are cashed out, then an equivalent credit of nonliquid points is granted
    payment_order = models.ForeignKey(PaymentOrder, on_delete=models.CASCADE)
    #only applicable if credit is a reward
    contributor_reward = models.ForeignKey(ContributorReward, on_delete=models.CASCADE)


class ContributorAccountDebit(TimeStampMixin, UUIDMixin):
    DebitReason = (
        (1, "LIQUIDATION"),
        (2, "PUNISHMENT"),
    )
    reason = models.IntegerField(choices=DebitReason, default=0)
    contributor_account = models.ForeignKey(ContributorAccount, on_delete=models.CASCADE)
    number_of_points = models.PositiveIntegerField()
    type_of_points = models.IntegerField(choices=PointTypes.choices(), default=PointTypes.NONLIQUID)
    payment_order = models.ForeignKey(PaymentOrder, on_delete=models.CASCADE)


class PointPriceConfiguration(TimeStampMixin, UUIDMixin):
    applicable_from_date = models.DateField()
    usd_point_inbound_price_in_cents = models.IntegerField()
    eur_point_inbound_price_in_cents = models.IntegerField()
    gbp_point_inbound_price_in_cents = models.IntegerField()
    usd_point_outbound_price_in_cents = models.IntegerField()
    eur_point_outbound_price_in_cents = models.IntegerField()
    gbp_point_outbound_price_in_cents = models.IntegerField()


    @staticmethod
    def get_point_inbound_price_in_cents(currency):
        conversion_rate_queryset = PointPriceConfiguration.objects.filter(applicable_from_date__lte=datetime.date.today()).order_by('-created_at')
        conversion_rates = conversion_rate_queryset.first()

        if currency == CurrencyTypes.USD:
            return conversion_rates.usd_point_inbound_price_in_cents
        elif currency == CurrencyTypes.EUR:
            return conversion_rates.eur_point_inbound_price_in_cents
        elif currency == CurrencyTypes.GBP:
            return conversion_rates.gbp_point_inbound_price_in_cents
        else:
            raise ValueError('No conversion rate for given currency.', currency)


