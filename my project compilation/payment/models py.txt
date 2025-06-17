# apps/payment/models.py

from django.db import models
from django.utils import timezone
from django.conf import settings # Import settings to reference AUTH_USER_MODEL
from apps.individual.models import Individual # Import Individual model
from apps.church.models import Church # Import Church model - assuming this exists in your project
from django.db.models import Max # Para makita ang Max nga receipt number
import datetime # Para sa date formatting sa receipt number

# Your existing ContributionType model (No changes needed based on your provided code)
class ContributionType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # Ensure default is 0.00

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Contribution Type"
        verbose_name_plural = "Contribution Types"
        ordering = ['name']


# NEW INTERMEDIARY MODEL: PaymentIndividualAllocation (Exactly as you provided)
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


# Function para mag-generate og bag-ong receipt number
# Kini ang atong basehan sa auto-generated numbers
def generate_receipt_number():
    today = timezone.localdate()
    prefix = today.strftime("OR-%Y-%m-") # Format: OR-YYYY-MM-
    
    # Pangitaon ang pinaka-taas nga sequential number para sa karong buwan
    # Kinahanglan nga dili ni 'legacy' records
    # Filter lang sa mga resibo nga nagsugod sa atong prefix
    last_receipt = Payment.objects.filter(
        receipt_number__startswith=prefix,
        is_legacy_record=False # Dili iapil ang legacy records
    ).aggregate(max_receipt=Max('receipt_number'))['max_receipt']

    if last_receipt:
        try:
            # I-extract ang sequential number (e.g., gikan sa "OR-2025-06-0001" kuhaon ang "0001")
            last_seq_str = last_receipt.split('-')[-1]
            last_seq_num = int(last_seq_str)
            next_seq_num = last_seq_num + 1
        except (ValueError, IndexError):
            # Fallback if parsing fails, magsugod og balik sa 1
            next_seq_num = 1
    else:
        next_seq_num = 1

    # I-format ang sunod nga sequential number (e.g., 1 -> "0001", 12 -> "0012")
    return f"{prefix}{next_seq_num:04d}" # 4 digits, padded with zeros


# Your Payment model (Integrated with your latest structure and audit requirements)
class Payment(models.Model):
    # Payment Method Choices as per your plan (GCash, Cash)
    PAYMENT_METHOD_CHOICES = [
        ('GCASH', 'GCash to GCash'),
        ('CASH', 'Cash on Hand'),
    ]

    # Payment Status Choices - IMPORTANTE NI PARA SA AUDITOR UG VALIDATION FLOW!
    PAYMENT_STATUS_CHOICES = [
        ('PENDING_VALIDATION', 'Pending Validation'), # Payments from Church In-charge
        ('VALIDATED', 'Validated'),                   # Confirmed by Admin/Cashier
        ('CANCELLED', 'Cancelled'),                   # Cancelled transaction
        ('DRAFT', 'Draft'),                           # Optional: For incomplete records
        ('COMPLETED', 'Completed'),                   # Fully processed (can combine with VALIDATED)
        ('LEGACY', 'Legacy Record'),                  # BAG-ONG ADD: Para sa old records nga walay OR
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
    
    # === CRITICAL CHANGE: receipt_number is now unique=False ===
    # This allows multiple 'legacy' records to have blank/null receipt numbers.
    # Uniqueness for 'active' new receipts will be enforced in Python logic.
    receipt_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=False, # CHANGED: From True to False to allow multiple blank/null values
        help_text="Official Receipt (OR) number or internal reference."
    )
    
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Who created/updated the record
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Reference Django's user model
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
        default='PENDING_VALIDATION', # Default status for new payments
        help_text="Current status of the payment (e.g., Pending Validation, Validated, Cancelled, Legacy)."
    )

    # Fields for validation workflow
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

    # Fields for cancellation (exactly as you provided)
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

    # Field to identify old records without physical OR
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

    # Many-to-Many field for covered members with through model
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
        ordering = ['-date_paid', '-created_at'] # Default ordering

    def __str__(self):
        or_display = self.receipt_number if self.receipt_number else "N/A"
        return f"Payment by {self.individual.full_name if self.individual else 'N/A'} (₱{self.amount:.2f}) - OR: {or_display} [{self.payment_status}]"

    def save(self, *args, **kwargs):
        # Auto-set created_by and updated_by based on request_user (if available)
        if not self.pk: # Only on creation (new record)
            if hasattr(self, '_request_user') and self._request_user.is_authenticated:
                self.created_by = self._request_user
            
            # --- RECEIPT NUMBER GENERATION LOGIC ---
            if self.is_legacy_record:
                # If it's a legacy record, ensure no auto-generation. Receipt number can be blank.
                # Set payment status to LEGACY if not already set.
                if not self.receipt_number: # Make sure it's explicitly blank/null if no OR
                    self.receipt_number = None
                if self.payment_status != 'CANCELLED': # Don't override 'CANCELLED' if user somehow marked legacy and cancelled
                    self.payment_status = 'LEGACY'
            elif not self.receipt_number: # If not a legacy record and receipt_number is empty
                # Generate a new receipt number
                self.receipt_number = generate_receipt_number()
                # Ensure it's unique among non-legacy records
                while Payment.objects.filter(
                    receipt_number=self.receipt_number,
                    is_legacy_record=False,
                    payment_status__in=['PENDING_VALIDATION', 'VALIDATED', 'COMPLETED', 'DRAFT'] # Only check active-like statuses
                ).exclude(pk=self.pk).exists(): # Exclude current instance for updates
                    # If it's not unique, try generating another one (unlikely but good safeguard)
                    self.receipt_number = generate_receipt_number()
            # If it's a new, non-legacy record, but receipt_number was already provided (e.g., from form input),
            # ensure its uniqueness too. This is a safeguard if the field is ever made editable on creation.
            elif Payment.objects.filter(
                receipt_number=self.receipt_number,
                is_legacy_record=False,
                payment_status__in=['PENDING_VALIDATION', 'VALIDATED', 'COMPLETED', 'DRAFT']
            ).exclude(pk=self.pk).exists():
                raise Exception("Receipt number already exists for an active, non-legacy payment. Please check.")
            # --- END RECEIPT NUMBER GENERATION LOGIC ---
        
        # Always update updated_by on save (for existing records or after creation logic)
        if hasattr(self, '_request_user') and self._request_user.is_authenticated:
            self.updated_by = self._request_user

        # Handle validation status and date/user
        if self.payment_status == 'VALIDATED' and not self.validation_date:
            self.validation_date = timezone.now()
            if hasattr(self, '_request_user') and self._request_user.is_authenticated:
                self.validated_by = self._request_user
        # If status changes FROM VALIDATED, clear validation info
        elif self.payment_status != 'VALIDATED' and self.validation_date:
            self.validation_date = None
            self.validated_by = None

        # Handle cancellation status and date/user
        # Note: 'is_cancelled' is directly tied to 'payment_status' becoming 'CANCELLED'
        if self.is_cancelled and not self.cancellation_date:
            self.cancellation_date = timezone.now()
            if hasattr(self, '_request_user') and self._request_user.is_authenticated:
                self.cancelled_by = self._request_user
            # Ensure payment_status is 'CANCELLED' if is_cancelled is True
            self.payment_status = 'CANCELLED' 
        elif not self.is_cancelled and self.cancellation_date:
            # If payment is uncancelled, clear cancellation info.
            # IMPORTANT: Decide how to reset payment_status if uncancelled.
            # For now, it remains as is, but you might want to revert to 'PENDING_VALIDATION'
            # or 'VALIDATED' based on specific business rules.
            self.cancellation_date = None
            self.cancelled_by = None
            # If payment was CANCELLED and now uncancelled, consider its previous non-cancelled state.
            # This complex logic might be better handled in your view or a dedicated method.
            # For simplicity, if uncancelled, we don't automatically change payment_status from CANCELLED
            # unless there's an explicit flow to re-activate it.
            # If you want to revert to PENDING_VALIDATION when uncancelled, add:
            # if self.payment_status == 'CANCELLED':
            #     self.payment_status = 'PENDING_VALIDATION' # Or 'DRAFT' or 'VALIDATED' if it was valid before.
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('payment:payment_detail', kwargs={'pk': self.pk})

