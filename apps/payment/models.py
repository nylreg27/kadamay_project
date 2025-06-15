# apps/payment/models.py

from django.db import models
from apps.individual.models import Individual
from django.utils import timezone
from django.conf import settings


class ContributionType(models.Model):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Payment(models.Model):
    # Payee: The individual who made the payment
    individual = models.ForeignKey(
        Individual,
        on_delete=models.PROTECT,
        related_name='payments_made',
        verbose_name="Payee"
    )

    # Optional: If you need to link to a family, not just an individual
    # family = models.ForeignKey(Family, on_delete=models.PROTECT,
    #                           related_name='family_payments', blank=True, null=True)

    contribution_type = models.ForeignKey(
        ContributionType, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_paid = models.DateField(default=timezone.now)

    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Cheque', 'Cheque'),
        ('Online', 'Online Payment'),
        ('Other', 'Other'),
    ]
    payment_method = models.CharField(
        max_length=50, choices=PAYMENT_METHOD_CHOICES, default='Cash')

    # Original receipt_no field - we will keep this as it might be used for external receipt numbers
    receipt_no = models.CharField(
        # Changed unique=True to unique=False as serial number will be the true unique identifier
        max_length=50, unique=False, blank=True, null=True)

    notes = models.TextField(
        blank=True, null=True, verbose_name="Remarks")  # Use for Remarks

    # Covered Members: Individuals covered by this payment (ManyToMany)
    covered_members = models.ManyToManyField(
        Individual,
        related_name='payments_covered',
        blank=True,
        help_text="Select members covered by this payment."
    )

    # --- BAG-ONG FIELDS KARON (Serial Number, Status, Audit Fields) ---

    # 1. Receipt Serial Number
    # Kini ang internal unique serial number para sa resibo.
    receipt_serial_number = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        verbose_name="System Receipt No.",
        help_text="Automatically generated unique receipt serial number."
    )

    # 2. Payment Status for Two-Step Validation
    STATUS_CHOICES = [
        ('PENDING', 'Pending Validation'),
        ('VALIDATED', 'Validated'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Payment Status",
        help_text="Current status of the payment (e.g., Pending, Validated, Cancelled)."
    )

    # 3. Cancellation Fields
    is_cancelled = models.BooleanField(
        default=False,
        verbose_name="Is Cancelled?",
        help_text="Check if this payment record has been cancelled."
    )
    cancellation_remarks = models.TextField(
        blank=True,
        null=True,
        verbose_name="Cancellation Remarks",
        help_text="Reason for cancellation, if applicable."
    )

    # 4. Audit Fields
    # User who initially recorded the payment (the 'incharge' user)
    encoded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_encoded',
        verbose_name="Encoded By"
    )
    encoded_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Encoded Date"
    )

    # User who validated the payment (the 'cashier' user)
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_validated',
        verbose_name="Validated By"
    )
    validated_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Validated Date"
    )  # This will be set manually upon validation

    # User who last edited the payment (if allowed)
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_edited',
        verbose_name="Last Edited By"
    )
    edited_date = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True,
        verbose_name="Last Edited Date"
    )

    # Original created_at and updated_at are still useful for general record tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True) # REMOVE THIS LINE, replace by encoded_by

    class Meta:
        ordering = ['-date_paid', '-created_at']
        verbose_name = "Payment/Contribution"
        verbose_name_plural = "Payment/Contributions"

    def __str__(self):
        return f"{self.individual.full_name} - {self.contribution_type.name} ({self.amount})"
