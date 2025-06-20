# apps/payment/models.py

from django.db import models
from django.utils import timezone
# Import for ForeignKey to User model
from django.contrib.auth import get_user_model

# Import related models from other apps
# MAKE SURE these import paths are correct based on your project structure!
# For example, if 'individual' app is in 'apps' directory.
from apps.individual.models import Individual
from apps.church.models import Church
from apps.contribution_type.models import ContributionType
from django.conf import settings

User = get_user_model()  # Get the currently active User model


class Payment(models.Model):
    or_number = models.CharField(
        max_length=20, unique=True, verbose_name="OR Number")

    # Existing fields...
    individual = models.ForeignKey(
        'individual.Individual',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_made',
        verbose_name="Payer (Main Individual)"
    )
    church = models.ForeignKey(
        'church.Church',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_received',
        verbose_name="Assigned Church"
    )
    contribution_type = models.ForeignKey(
        'contribution_type.ContributionType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name="Contribution Type"
    )
    amount_paid = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Amount Paid")
    date_paid = models.DateField(
        default=timezone.now, verbose_name="Date Paid")
    notes = models.TextField(
        blank=True, null=True, verbose_name="Payment Notes")

    # --- New/Updated Fields based on our discussions ---
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('gcash', 'GCash'),
        # Add other methods as needed
    ]
    payment_method = models.CharField(
        max_length=10, choices=PAYMENT_METHOD_CHOICES, default='cash', verbose_name="Payment Method")

    gcash_reference_number = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="GCash Reference No."
    )

    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('pending', 'Pending Validation (GCash)'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='paid', verbose_name="Status"
    )

    # Audit fields:
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_created',
        verbose_name="Created By"
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_updated',
        verbose_name="Last Updated By"
    )
    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_collected',
        verbose_name="Collected By"
    )
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_validated',
        verbose_name="Validated By"
    )
    validated_at = models.DateTimeField(
        blank=True, null=True, verbose_name="Validated At"
    )
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_cancelled',
        verbose_name="Cancelled By"
    )
    cancellation_reason = models.TextField(
        blank=True, null=True, verbose_name="Cancellation Reason"
    )
    cancelled_at = models.DateTimeField(
        blank=True, null=True, verbose_name="Cancelled At"
    )

    class Meta:
        verbose_name = 'Payment Record'
        verbose_name_plural = 'Payment Records'
        ordering = ['-date_paid', '-or_number']

    def __str__(self):
        return f"OR #{self.or_number} - {self.individual.full_name if self.individual else 'N/A'} - {self.amount_paid}"

    @property
    def is_cancelled(self):
        return self.status == 'cancelled'

    @property
    def is_pending_gcash(self):
        return self.status == 'pending' and self.payment_method == 'gcash'

# ... (CoveredMember model and other related models if any) ...


class CoveredMember(models.Model):
    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name='covered_members'
    )
    individual = models.ForeignKey(
        'individual.Individual', on_delete=models.CASCADE
    )
    # You might want to add amount_covered field here if each member pays a specific part
    # amount_covered = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        # A member can only be covered once per payment
        unique_together = ('payment', 'individual')
        verbose_name = 'Covered Member'
        verbose_name_plural = 'Covered Members'

    def __str__(self):
        return f"{self.individual.full_name} covered by OR #{self.payment.or_number}"
