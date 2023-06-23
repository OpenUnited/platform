from backend.mixins import TimeStampMixin, UUIDMixin
from django.db import models
from django.db.models import Sum
from .utils import *
import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver
from model_utils import FieldTracker
from notifications.signals import notify

import notification.tasks
from backend.mixins import TimeStampMixin, UUIDMixin
from notification.models import Notification
from talent.models import Person
from work.models import Bounty

CLAIM_TYPE_DONE = 0
CLAIM_TYPE_ACTIVE = 1
CLAIM_TYPE_FAILED = 2
CLAIM_TYPE_IN_REVIEW = 3


class BountyClaim(TimeStampMixin, UUIDMixin):
    CLAIM_TYPE = (
        (CLAIM_TYPE_DONE, "Done"),
        (CLAIM_TYPE_ACTIVE, "Active"),
        (CLAIM_TYPE_FAILED, "Failed"),
        (CLAIM_TYPE_IN_REVIEW, "In review")
    )
    bounty = models.ForeignKey(Bounty, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True)
    kind = models.IntegerField(choices=CLAIM_TYPE, default=0)
    tracker = FieldTracker()

    def __str__(self):
        return '{}: {} ({})'.format(self.bounty.challenge, self.person, self.kind)


@receiver(post_save, sender=BountyClaim)
def save_bounty_claim(sender, instance, created, **kwargs):
    challenge = instance.bounty.challenge
    reviewer = getattr(challenge, "reviewer", None)
    contributor = instance.person
    contributor_email = contributor.email_address
    reviewer_user = reviewer.user if reviewer else None

    if not created:
        # contributor has submitted the work for review
        if instance.kind == CLAIM_TYPE_IN_REVIEW and instance.tracker.previous("kind") is not CLAIM_TYPE_IN_REVIEW:
            challenge = instance.bounty.challenge
            subject = f"The challenge \"{challenge.title}\" is ready to review"
            message = f"You can see the challenge here: {challenge.get_challenge_link()}"
            if reviewer:
                notify.send(instance, recipient=reviewer_user, verb=subject, description=message)
                notification.tasks.send_notification.delay([Notification.Type.EMAIL],
                                                           Notification.EventType.TASK_READY_TO_REVIEW,
                                                           receivers=[reviewer.id],
                                                           task_title=challenge.title,
                                                           task_link=challenge.get_challenge_link())


class BountyDeliveryAttempt(TimeStampMixin):
    SUBMISSION_TYPE_NEW = 0
    SUBMISSION_TYPE_APPROVED = 1
    SUBMISSION_TYPE_REJECTED = 2

    SUBMISSION_TYPES = (
        (SUBMISSION_TYPE_NEW, "New"),
        (SUBMISSION_TYPE_APPROVED, "Approved"),
        (SUBMISSION_TYPE_REJECTED, "Rejected"),
    )
    
    kind = models.IntegerField(choices=SUBMISSION_TYPES, default=0)
    bounty_claim = models.ForeignKey(BountyClaim, on_delete=models.CASCADE, blank=True, null=True,
                                   related_name="delivery_attempt")
    person = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True)
    is_canceled = models.BooleanField(default=False)
    delivery_message = models.CharField(max_length=2000, default=None)
    tracker = FieldTracker()


class BountyDeliveryAttachment(models.Model):
    bounty_delivery_attempt = models.ForeignKey(BountyDeliveryAttempt, on_delete=models.CASCADE, related_name='attachments')
    file_type = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    path = models.CharField(max_length=100)


@receiver(post_save, sender=BountyDeliveryAttempt)
def save_bounty_claim_request(sender, instance, created, **kwargs):
    bounty_claim = instance.bounty_claim
    contributor = instance.person
    contributor_id = contributor.id
    reviewer = getattr(bounty_claim.bounty.challenge, "reviewer", None)
    reviewer_user = reviewer.user if reviewer else None

    # contributor request to claim it
    if created and not bounty_claim.bounty.challenge.auto_approve_task_claims:
        subject = f"A new bounty delivery attempt has been created"
        message = f"A new bounty delivery attempt has been created for the challenge: \"{bounty_claim.bounty.challenge.title}\""

        if reviewer:
            notify.send(instance, recipient=reviewer_user, verb=subject, description=message)
            notification.tasks.send_notification.delay([Notification.Type.EMAIL],
                                                       Notification.EventType.TASK_DELIVERY_ATTEMPT_CREATED,
                                                       receivers=[reviewer.id],
                                                       task_title=bounty_claim.bounty.challenge.title)
    if not created:
        # contributor quits the task
        if instance.is_canceled and not instance.tracker.previous("is_canceled"):
            subject = f"The contributor left the task"
            message = f"The contributor has left the task \"{bounty_claim.bounty.challenge.title}\""

            if reviewer:
                notify.send(instance, recipient=reviewer_user, verb=subject, description=message)
                notification.tasks.send_notification.delay([Notification.Type.EMAIL],
                                                           Notification.EventType.CONTRIBUTOR_LEFT_TASK,
                                                           receivers=[reviewer.id],
                                                           task_title=bounty_claim.bounty.challenge.title)



class OrganisationAccountCredit(TimeStampMixin, UUIDMixin):
    organisation_account = models.ForeignKey(to='OrganisationAccount', on_delete=models.CASCADE)
    number_of_points = models.PositiveIntegerField()
    type_of_points = models.IntegerField(choices=PointTypes.choices(), default=PointTypes.NONLIQUID)
    credit_reason = models.IntegerField(choices=OrganisationAccountCreditReasons.choices(), default=OrganisationAccountCreditReasons.GRANT)


class OrganisationAccount(models.Model):
    organisation = models.ForeignKey(to="commercial.Organisation", on_delete=models.CASCADE)
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
    product = models.ForeignKey(to="work.Product", on_delete=models.CASCADE)
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
    bounty_claim = models.ForeignKey(to="matching.BountyClaim", on_delete=models.CASCADE)
    number_of_points = models.PositiveIntegerField()
    type_of_points = models.IntegerField(choices=PointTypes.choices(), default=PointTypes.NONLIQUID)
    

class ProductAccountDebit(TimeStampMixin, UUIDMixin):
    bounty_claim = models.ForeignKey(to="matching.BountyClaim", on_delete=models.CASCADE)
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
        (1, "TASK"),
        (2, "LIQUIDATION"),
        (3, "REWARD")
    )
    reason = models.IntegerField(choices=CreditReason, default=0)
    bounty_claim = models.ForeignKey(to="matching.BountyClaim", on_delete=models.CASCADE)
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


