import uuid
from django.db import models
from openunited.mixins import TimeStampMixin, UUIDMixin
from django.contrib.contenttypes.fields import GenericRelation
from django.core.validators import RegexValidator

from openunited.mixins import TimeStampMixin, UUIDMixin
from product_management.models import Product
from .utils import *


class Organisation(TimeStampMixin):
    username = models.CharField(
        max_length=39,
        unique=True,
        default="",
        validators=[
            RegexValidator(
                regex="^[a-z0-9]*$",
                message="Username may only contain letters and numbers",
                code="invalid_username",
            )
        ],
    )
    name = models.CharField(max_length=512, unique=True)
    products = GenericRelation(Product)
    photo = models.ImageField(upload_to="avatars/", null=True, blank=True)

    class Meta:
        verbose_name_plural = "Organisations"

    def get_username(self):
        return self.username

    def __str__(self):
        return self.name


class OrganisationAccountCredit(TimeStampMixin, UUIDMixin):
    organisation_account = models.ForeignKey(
        to="OrganisationAccount", on_delete=models.CASCADE
    )
    number_of_points = models.PositiveIntegerField()
    type_of_points = models.IntegerField(
        choices=PointTypes.choices(), default=PointTypes.NONLIQUID
    )
    credit_reason = models.IntegerField(
        choices=OrganisationAccountCreditReasons.choices(),
        default=OrganisationAccountCreditReasons.GRANT,
    )


class OrganisationAccount(models.Model):
    organisation = models.ForeignKey(to="Organisation", on_delete=models.CASCADE)
    liquid_points_balance = models.PositiveBigIntegerField()
    nonliquid_points_balance = models.PositiveBigIntegerField()


class Cart(TimeStampMixin, UUIDMixin):
    organisation_account = models.ForeignKey(
        OrganisationAccount, on_delete=models.CASCADE
    )
    creator = models.ForeignKey(to="talent.Person", on_delete=models.CASCADE)
    number_of_points = models.IntegerField(default=500)
    currency_of_payment = models.IntegerField(
        choices=CurrencyTypes.choices(), default=CurrencyTypes.USD
    )
    price_per_point_in_cents = models.IntegerField()
    subtotal_in_cents = models.PositiveBigIntegerField()
    sales_tax_in_cents = models.PositiveBigIntegerField()
    total_payable_in_cents = models.PositiveBigIntegerField()
    payment_type = models.IntegerField(
        choices=PaymentTypes.choices(), default=PaymentTypes.ONLINE
    )


class Grant(models.Model):
    organisation_account = models.ForeignKey(
        OrganisationAccount, on_delete=models.CASCADE
    )
    nominating_bee_keeper = models.ForeignKey(
        to="talent.Person", on_delete=models.CASCADE, related_name="nominator"
    )
    approving_bee_keeper = models.ForeignKey(
        to="talent.Person", on_delete=models.CASCADE, related_name="approver"
    )
    description = models.TextField(max_length=1024)
    number_of_points = models.IntegerField(default=500)
    status = models.IntegerField(
        choices=LifecycleStatusOptions.choices(), default=LifecycleStatusOptions.NEW
    )
    organisation_account_credit = models.ForeignKey(
        to="OrganisationAccountCredit", on_delete=models.CASCADE, null=True
    )

    def mark_points_as_granted(self, credit):
        self.organisation_account_credit = credit
        self.status = LifecycleStatusOptions.COMPLETE
        self.save()


class SalesOrder(TimeStampMixin, UUIDMixin):
    organisation_account = models.ForeignKey(
        OrganisationAccount, on_delete=models.CASCADE
    )
    organisation_account_credit = models.ForeignKey(
        to="OrganisationAccountCredit", on_delete=models.CASCADE, null=True
    )
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    number_of_points = models.IntegerField()
    currency_of_payment = models.IntegerField(
        choices=CurrencyTypes.choices(), default=CurrencyTypes.USD
    )
    price_per_point_in_cents = models.IntegerField()
    subtotal_in_cents = models.PositiveBigIntegerField()
    sales_tax_in_cents = models.PositiveBigIntegerField()
    total_payable_in_cents = models.PositiveBigIntegerField()
    payment_type = models.IntegerField(
        choices=PaymentTypes.choices(), default=PaymentTypes.ONLINE
    )
    payment_status = models.IntegerField(
        choices=PaymentStatusOptions.choices(), default=PaymentStatusOptions.PENDING
    )
    process_status = models.IntegerField(
        choices=LifecycleStatusOptions.choices(), default=LifecycleStatusOptions.NEW
    )


class InboundPayment(TimeStampMixin, UUIDMixin):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE)
    payment_type = models.IntegerField(
        choices=PaymentTypes.choices(), default=PaymentTypes.ONLINE
    )
    currency_of_payment = models.IntegerField(
        choices=CurrencyTypes.choices(), default=CurrencyTypes.USD
    )
    amount_paid_in_cents = models.PositiveBigIntegerField()
    transaction_detail = models.TextField(max_length=1024)


class OrganisationAccountDebit(TimeStampMixin, UUIDMixin):
    DebitReason = (
        (1, "TRANSFER"),
        (2, "EXPIRY"),
    )
    organisation_account = models.ForeignKey(
        to="OrganisationAccount", on_delete=models.CASCADE
    )
    number_of_points = models.PositiveIntegerField
    type_of_points = models.IntegerField(
        choices=PointTypes.choices(), default=PointTypes.NONLIQUID
    )
    debit_reason = models.IntegerField(choices=DebitReason, default=0)


class ProductAccount(models.Model):
    product = models.ForeignKey(
        to="product_management.Product", on_delete=models.CASCADE
    )
    liquid_points_balance = models.PositiveBigIntegerField()
    nonliquid_points_balance = models.PositiveBigIntegerField()


class ProductAccountCredit(TimeStampMixin, UUIDMixin):
    # each product account credit has a matching organisation account debit
    organisation_account_debit = models.ForeignKey(
        OrganisationAccountDebit, on_delete=models.CASCADE
    )
    product_account = models.ForeignKey(ProductAccount, on_delete=models.CASCADE)
    number_of_points = models.PositiveIntegerField()
    type_of_points = models.IntegerField(
        choices=PointTypes.choices(), default=PointTypes.NONLIQUID
    )
    actioned_by = models.ForeignKey(to="talent.Person", on_delete=models.CASCADE)


class ProductAccountReservation(TimeStampMixin, UUIDMixin):
    bounty_claim = models.ForeignKey(to="talent.BountyClaim", on_delete=models.CASCADE)
    number_of_points = models.PositiveIntegerField()
    type_of_points = models.IntegerField(
        choices=PointTypes.choices(), default=PointTypes.NONLIQUID
    )


class ProductAccountDebit(TimeStampMixin, UUIDMixin):
    bounty_claim = models.ForeignKey(to="talent.BountyClaim", on_delete=models.CASCADE)
    number_of_points = models.PositiveIntegerField()
    type_of_points = models.IntegerField(
        choices=PointTypes.choices(), default=PointTypes.NONLIQUID
    )


class ContributorAccount(models.Model):
    owner = models.ForeignKey(to="talent.Person", on_delete=models.CASCADE)
    community_status = models.IntegerField(
        choices=CommunityStatusOptions.choices(), default=CommunityStatusOptions.DRONE
    )
    liquid_points_balance = models.PositiveBigIntegerField(default=0)
    nonliquid_points_balance = models.PositiveBigIntegerField(default=0)


class PaymentOrder(TimeStampMixin, UUIDMixin):
    contributor_account = models.ForeignKey(
        ContributorAccount, on_delete=models.CASCADE
    )
    currency_of_payment = models.IntegerField(
        choices=CurrencyTypes.choices(), default=CurrencyTypes.USD
    )
    subtotal_in_cents = models.PositiveBigIntegerField()
    sales_tax_in_cents = models.PositiveBigIntegerField()
    total_payable_in_cents = models.PositiveBigIntegerField()
    PaymentType = (
        (1, "PARTNER"),
        (2, "BANK TRANSFER"),
    )
    payment_type = models.IntegerField(choices=PaymentType, default=0)
    status = models.IntegerField(
        choices=LifecycleStatusOptions.choices(), default=LifecycleStatusOptions.NEW
    )


class OutboundPayment(TimeStampMixin, UUIDMixin):
    payment_order = models.ForeignKey(PaymentOrder, on_delete=models.CASCADE)
    details = models.TextField(max_length=1024)


class ContributorReward(TimeStampMixin, UUIDMixin):
    RewardedActions = (
        (1, "INVITED FRIENDS"),
        (2, "VERIFIED IDENTITY"),
    )
    contributor_account = models.ForeignKey(
        ContributorAccount, on_delete=models.CASCADE
    )
    action = models.IntegerField(choices=RewardedActions, default=0)
    points = models.IntegerField(default=10)


class ContributorAccountCredit(TimeStampMixin, UUIDMixin):
    CreditReason = ((1, "BOUNTY"), (2, "LIQUIDATION"), (3, "REWARD"))
    reason = models.IntegerField(choices=CreditReason, default=0)
    bounty_claim = models.ForeignKey(to="talent.BountyClaim", on_delete=models.CASCADE)
    contributor_account = models.ForeignKey(
        ContributorAccount, on_delete=models.CASCADE
    )
    number_of_points = models.PositiveIntegerField()
    type_of_points = models.IntegerField(
        choices=PointTypes.choices(), default=PointTypes.NONLIQUID
    )
    # when liquid points are cashed out, then an equivalent credit of nonliquid points is granted
    payment_order = models.ForeignKey(PaymentOrder, on_delete=models.CASCADE)
    # only applicable if credit is a reward
    contributor_reward = models.ForeignKey(ContributorReward, on_delete=models.CASCADE)


class ContributorAccountDebit(TimeStampMixin, UUIDMixin):
    DebitReason = (
        (1, "LIQUIDATION"),
        (2, "PUNISHMENT"),
    )
    reason = models.IntegerField(choices=DebitReason, default=0)
    contributor_account = models.ForeignKey(
        ContributorAccount, on_delete=models.CASCADE
    )
    number_of_points = models.PositiveIntegerField()
    type_of_points = models.IntegerField(
        choices=PointTypes.choices(), default=PointTypes.NONLIQUID
    )
    payment_order = models.ForeignKey(PaymentOrder, on_delete=models.CASCADE)


class PointPriceConfiguration(TimeStampMixin, UUIDMixin):
    applicable_from_date = models.DateField()
    usd_point_inbound_price_in_cents = models.IntegerField()
    eur_point_inbound_price_in_cents = models.IntegerField()
    gbp_point_inbound_price_in_cents = models.IntegerField()
    usd_point_outbound_price_in_cents = models.IntegerField()
    eur_point_outbound_price_in_cents = models.IntegerField()
    gbp_point_outbound_price_in_cents = models.IntegerField()
