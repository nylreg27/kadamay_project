# apps/payment/models.py
from django.db import models
from apps.individual.models import Individual
from apps.contribution_type.models import ContributionType
from django.contrib.auth import get_user_model

User = get_user_model()


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('gcash', 'GCash'),
    ]

    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('pending', 'Pending (for GCash validation)'),
        ('cancelled', 'Cancelled'),
    ]

    # KINI ANG KAUSABAN: Gihimo ni natong null=True ug blank=True
    # para maka-accommodate sa payments nga walay OR number
    or_number = models.CharField(
        max_length=50, unique=True, null=True, blank=True, verbose_name="Official Receipt No.")

    individual = models.ForeignKey(
        Individual, on_delete=models.CASCADE, related_name='payments_made', verbose_name="Payer/Member")
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Amount Paid")
    date_paid = models.DateField(verbose_name="Date Paid")
    payment_method = models.CharField(
        max_length=10, choices=PAYMENT_METHOD_CHOICES, default='cash', verbose_name="Payment Method")
    gcash_reference_number = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="GCash Reference Number")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='paid', verbose_name="Payment Status")
    collected_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Collected By")
    contribution_type = models.ForeignKey(
        ContributionType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Contribution Type")

    # BAG-ONG ADDED FIELDS PARA SA AUDITORS PURPOSE, BRO!
    validated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments_validated',
        verbose_name="Validated By", help_text="User who validated the payment (e.g., for GCash)")
    cancelled_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments_cancelled',
        verbose_name="Cancelled By", help_text="User who cancelled the payment")
    date_validated = models.DateTimeField(
        null=True, blank=True, verbose_name="Date Validated")
    date_cancelled = models.DateTimeField(
        null=True, blank=True, verbose_name="Date Cancelled")
    cancellation_reason = models.TextField(
        blank=True, verbose_name="Cancellation Reason")

    # This M2M field is fine, just ensure the through model has the amount_covered field
    covered_members = models.ManyToManyField(
        Individual, through='PaymentCoveredMember', related_name='payments_covered', verbose_name="Members Covered by this Payment")

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        # Mag-ampo ta nga dili magkagubot sa ordering kung null ang or_number, pero sa date_paid ra man gihapon ang primary.
        ordering = ['-date_paid', '-or_number']

    def __str__(self):
        # I-handle ang kaso kung null ang or_number
        or_str = self.or_number if self.or_number else "NO OR"
        return f"OR {or_str} - {self.amount} ({self.individual.full_name if self.individual else 'N/A'})"

    def get_full_name(self):
        return f"{self.individual.given_name} {self.individual.surname}"


# THIS IS THE PaymentCoveredMember MODEL THAT NEEDS TO BE IN models.py
class PaymentCoveredMember(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    individual = models.ForeignKey(
        Individual, on_delete=models.CASCADE, verbose_name="Member Covered")
    amount_covered = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Amount Covered")

    class Meta:
        verbose_name = "Member Covered"
        verbose_name_plural = "Members Covered"
        unique_together = ('payment', 'individual')

    def __str__(self):
        return f"{self.individual.full_name if self.individual else 'N/A'} (for OR #{self.payment.or_number if self.payment.or_number else 'NO OR'})"
