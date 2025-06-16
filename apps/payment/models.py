# apps/payment/models.py

from django.db import models
from django.utils import timezone
from django.conf import settings
from apps.individual.models import Individual
from apps.church.models import Church


# Your existing ContributionType model (no changes needed here for now)
class ContributionType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Contribution Type"
        verbose_name_plural = "Contribution Types"
        ordering = ['name']


# NEW INTERMEDIARY MODEL: PaymentIndividualAllocation - DUGANGAN OG is_payer
class PaymentIndividualAllocation(models.Model):
    payment = models.ForeignKey(
        'Payment',
        on_delete=models.CASCADE,
        related_name='individual_allocations'
    )
    individual = models.ForeignKey(
        Individual,
        on_delete=models.CASCADE,
        related_name='payment_allocations'
    )
    allocated_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # NEW FIELD: Is this individual the actual payer for this specific allocation?
    is_payer = models.BooleanField(
        default=False,
        help_text="True if this individual is the actual payer of this allocated amount."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('payment', 'individual')
        verbose_name = "Payment Individual Allocation"
        verbose_name_plural = "Payment Individual Allocations"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.individual.full_name} - ₱{self.allocated_amount} from Payment #{self.payment.id}"


# Your Payment model (no changes needed here for this fix)
class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('GCASH', 'GCash to GCash'),
        ('CASH', 'Cash on Hand'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PENDING_VALIDATION', 'Pending Validation'),
        ('VALIDATED', 'Validated'),
        ('CANCELLED', 'Cancelled'),
        ('DRAFT', 'Draft'),
        ('COMPLETED', 'Completed'),
    ]

    individual = models.ForeignKey(
        Individual,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    church = models.ForeignKey(
        Church,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    contribution_type = models.ForeignKey(
        ContributionType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    date_paid = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    receipt_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text="Official Receipt (OR) number or internal reference."
    )
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_updated'
    )

    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        default='CASH',
        help_text="Method of payment (e.g., Cash, GCash)."
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING_VALIDATION',
        help_text="Current status of the payment (e.g., Pending Validation, Validated, Cancelled)."
    )

    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_collected',
        help_text="User who initially collected the payment (e.g., Church In-charge)."
    )
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_validated',
        help_text="Admin/Cashier who validated the payment."
    )
    validation_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time when the payment was validated."
    )

    is_cancelled = models.BooleanField(
        default=False,
        help_text="Indicates if the receipt/payment has been cancelled."
    )
    cancellation_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for cancelling the payment, if applicable."
    )
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_cancelled',
        help_text="User who marked the payment as cancelled."
    )
    cancellation_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time when the payment was cancelled."
    )

    is_legacy_record = models.BooleanField(
        default=False,
        help_text="True if this is an old record without a physical official receipt number."
    )

    deceased_member = models.ForeignKey(
        Individual,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_for_deceased',
        help_text="If this payment is for a deceased member's contribution."
    )

    covered_members = models.ManyToManyField(
        Individual,
        through='PaymentIndividualAllocation',
        related_name='payments_covered',
        blank=True,
        help_text="Individuals covered by this payment, with specific allocated amounts."
    )

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ['-date_paid', '-created_at']

    def __str__(self):
        return f"Payment by {self.individual.full_name if self.individual else 'N/A'} - {self.amount}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('payment:payment_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if not self.pk:
            if hasattr(self, '_request_user') and self._request_user.is_authenticated:
                self.created_by = self._request_user

        if hasattr(self, '_request_user') and self._request_user.is_authenticated:
            self.updated_by = self._request_user

        if self.payment_status == 'VALIDATED' and not self.validation_date:
            self.validation_date = timezone.now()
            if hasattr(self, '_request_user') and self._request_user.is_authenticated:
                self.validated_by = self._request_user

        if self.is_cancelled and not self.cancellation_date:
            self.cancellation_date = timezone.now()
            if hasattr(self, '_request_user') and self._request_user.is_authenticated:
                self.cancelled_by = self._request_user

        super().save(*args, **kwargs)
