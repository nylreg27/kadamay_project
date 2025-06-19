# apps/payment/models.py

from django.db import models
from django.utils import timezone
from django.conf import settings # Import settings to reference AUTH_USER_MODEL
from apps.individual.models import Individual # Import Individual model - Assuming 'individual' app is also inside 'apps' folder
from apps.church.models import Church # Import Church model - assuming this exists in your project
from django.db.models import Max # Para makita ang Max nga receipt number
from apps.family.models import Family # Import Family model (if needed for context)
from django.db.models import Sum
import datetime # Para sa date formatting sa receipt number
import re # Para sa regular expression sa OR number parsing

# Your existing ContributionType model
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


# Helper function para mag-generate og sunod nga sequential number para sa YY-NNNN format
def get_next_yy_sequential_number(model_class, receipt_number_field='receipt_number'):
    """
    Generates the next sequential number for the 'YY-NNNN' format,
    where YY is the last two digits of the current year, and NNNN is a 4-digit sequential number
    that resets every year.
    """
    current_year_two_digits = datetime.date.today().strftime("%y")
    prefix = f"{current_year_two_digits}-"

    # Find the highest existing sequential number for the current year's prefix
    # We use __startswith to match the year prefix, and a regex to ensure it's exactly YY-NNNN
    last_record = model_class.objects.filter(
        **{f"{receipt_number_field}__startswith": prefix},
        is_legacy_record=False, # Exclude legacy records from numbering sequence
        # Use regex to ensure the format is exactly YY-NNNN, not just starts with YY-
        # This prevents issues if a different format accidentally starts with YY-
        **{f"{receipt_number_field}__regex": r'^' + re.escape(prefix) + r'\d{4}$'}
    ).order_by(f'-{receipt_number_field}').first()

    next_seq_num = 1
    if last_record and getattr(last_record, receipt_number_field):
        try:
            # Extract the numerical part (NNNN) from the receipt number
            # Example: '25-0001' -> '0001'
            numerical_part_str = getattr(last_record, receipt_number_field).split('-')[-1]
            last_seq_num = int(numerical_part_str)
            next_seq_num = last_seq_num + 1
        except (ValueError, IndexError):
            # If parsing fails, reset to 1
            next_seq_num = 1
    
    return f"{prefix}{next_seq_num:04d}" # Always 4 digits for the sequential part (e.g., '25-0001')


# Your Payment model
class Payment(models.Model):
    # Payment Method Choices
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
        ('LEGACY', 'Legacy Record'),                  # Para sa old records nga walay OR
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
        unique=False, # Keep unique=False here, uniqueness will be managed by save method
        help_text="Official Receipt (OR) number or internal reference. Auto-generated for new payments (YY-NNNN format)."
    )
    
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Who created/updated the record
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
        help_text="Current status of the payment (e.g., Pending Validation, Validated, Cancelled, Legacy)."
    )

    # NEW FIELD: For GCash payments
    gcash_reference_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Reference number for GCash transactions (e.g., transaction ID)."
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

    # Fields for cancellation
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
        through='CoveredMember', 
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
            
            # === RECEIPT NUMBER GENERATION LOGIC (YY-NNNN FORMAT) ===
            if self.is_legacy_record:
                if not self.receipt_number: 
                    self.receipt_number = None # Ensure it's explicitly null/blank for legacy
                # Only set to LEGACY if not already CANCELLED by a specific action or explicitly set
                if self.payment_status not in ['CANCELLED', 'LEGACY']: 
                    self.payment_status = 'LEGACY'
            elif not self.receipt_number: # If not legacy and receipt_number is empty (needs auto-gen)
                self.receipt_number = get_next_yy_sequential_number(
                    model_class=Payment, 
                    receipt_number_field='receipt_number'
                )
            # If receipt_number was manually provided for a non-legacy record,
            # ensure its uniqueness for active payments.
            if self.receipt_number and not self.is_legacy_record:
                if Payment.objects.filter(
                    receipt_number=self.receipt_number,
                    is_legacy_record=False,
                    payment_status__in=['PENDING_VALIDATION', 'VALIDATED', 'COMPLETED', 'DRAFT'] 
                ).exclude(pk=self.pk).exists():
                    raise ValueError(f"Receipt number '{self.receipt_number}' already exists for an active, non-legacy payment. Please provide a unique number or leave blank to auto-generate.")
            # === END RECEIPT NUMBER GENERATION LOGIC ===
        
        # Always update updated_by on save (for existing records or after creation logic)
        if hasattr(self, '_request_user') and self._request_user.is_authenticated:
            self.updated_by = self._request_user

        # Handle validation status and date/user
        if self.payment_status == 'VALIDATED' and not self.validation_date:
            self.validation_date = timezone.now()
            if hasattr(self, '_request_user') and self._request_user.is_authenticated:
                self.validated_by = self._request_user
        elif self.payment_status != 'VALIDATED' and self.validation_date:
            self.validation_date = None
            self.validated_by = None

        # Handle cancellation status and date/user
        if self.is_cancelled and not self.cancellation_date:
            self.cancellation_date = timezone.now()
            if hasattr(self, '_request_user') and self._request_user.is_authenticated:
                self.cancelled_by = self._request_user
            self.payment_status = 'CANCELLED' 
        elif not self.is_cancelled and self.cancellation_date:
            self.cancellation_date = None
            self.cancelled_by = None
            # If payment was CANCELLED and now uncancelled, consider its previous non-cancelled state.
            # This complex logic might be better handled in your view or a dedicated method.
            # For simplicity, if uncancelled, we don't automatically change payment_status from CANCELLED
            # unless there's an explicit flow to re-activate it.
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('payment:payment_detail', kwargs={'pk': self.pk})


    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    # Add any other fields relevant to contribution types, e.g., default_amount

    class Meta:
        verbose_name_plural = "Contribution Types"
        ordering = ['name']

    def __str__(self):
        return self.name

# --- DEFINE CHOICES HERE ---
PAYMENT_METHOD_CHOICES = [
    ('CASH', 'Cash'),
    ('GCASH', 'GCash'),
]

PAYMENT_STATUS_CHOICES = [
    ('PAID', 'Paid'),
    ('PENDING_VALIDATION', 'Pending Validation'),
    ('CANCELLED', 'Cancelled'),
]

CONTRIBUTION_TYPE_CHOICES = [
    ('ANNUAL_FEE', 'Annual Fee'),
    ('MORTUARY_AID', 'Mortuary Aid'),
    ('DONATION', 'Donation'),
    ('SPECIAL_ASSESSMENT', 'Special Assessment'),
    # Add other types as needed
]
class Payment(models.Model):
    receipt_number = models.CharField(max_length=50, unique=True, db_index=True) # Official Receipt Number
    date_paid = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='CASH')
    gcash_reference_number = models.CharField(max_length=100, blank=True, null=True, help_text="Required if Payment Method is GCash")
    
    # Relationships
    church = models.ForeignKey(Church, on_delete=models.SET_NULL, null=True, blank=True,
                               help_text="Church where payment was collected or associated with")
    collected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                     related_name='payments_collected',
                                     help_text="User who collected the payment (Cashier/InCharge)")
    
    # Contribution Type (e.g., Annual Fee, Mortuary Aid, Donation)
    contribution_type = models.ForeignKey(ContributionType, on_delete=models.SET_NULL, null=True, blank=True)

    # Status and Audit fields
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PAID') # PAID, PENDING_VALIDATION, CANCELLED
    
    validated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='payments_validated',
                                     help_text="Admin who validated GCash payment",
                                     verbose_name="Validated By (Admin Only)")
    validation_date = models.DateTimeField(null=True, blank=True)
    
    is_cancelled = models.BooleanField(default=False)
    cancellation_date = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    cancelled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='payments_cancelled',
                                     help_text="User who cancelled the payment")

    notes = models.TextField(blank=True, null=True)
    is_legacy_record = models.BooleanField(default=False, help_text="Indicates if this is a record imported from an old system.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='payment_created_by')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='payment_updated_by')

    # This field is for a single individual paying for themselves directly (if no 'covered_members' are selected)
    # This might be redundant if ALL payments will have covered_members. Let's keep it optional for now.
    individual = models.ForeignKey(Individual, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='payments_made_by_self',
                                   help_text="The individual who made the payment (if not covered by another)")

    # For deceased member related payments (e.g., Mortuary Aid for a specific deceased)
    deceased_member = models.ForeignKey(Individual, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='payments_for_deceased',
                                        help_text="If this payment is related to a deceased member (e.g., Mortuary Aid).")

    class Meta:
        ordering = ['-date_paid', '-receipt_number']
        verbose_name_plural = "Payments"

    def __str__(self):
        return f"OR #{self.receipt_number} - {self.amount:.2f} on {self.date_paid}"

    def save(self, *args, **kwargs):
        # Set validation_date if payment_status is validated and not set
        if self.payment_status == 'PAID' and self.payment_method == 'GCASH' and not self.validation_date:
            self.validation_date = models.DateTimeField.now()
        
        # Handle cancellation logic
        if self.is_cancelled and not self.cancellation_date:
            self.cancellation_date = models.DateTimeField.now()
        elif not self.is_cancelled and self.cancellation_date:
            self.cancellation_date = None
            self.cancellation_reason = None
            self.cancelled_by = None

        super().save(*args, **kwargs)

    @property
    def total_covered_amount(self):
        # Calculates the sum of amounts allocated to covered members for this payment
        return self.covered_members.aggregate(total_amount=Sum('amount_allocated'))['total_amount'] or 0

    @property
    def get_payees_display(self):
        # Returns a comma-separated list of names of covered members
        payees_names = [cm.individual.full_name for cm in self.covered_members.all()]
        return ", ".join(payees_names) if payees_names else "N/A"


class CoveredMember(models.Model):
    """
    This model links a Payment to multiple Individuals who are covered by that payment.
    It also stores the specific amount allocated to each individual from the total payment.
    """
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='covered_members')
    individual = models.ForeignKey(Individual, on_delete=models.CASCADE, related_name='payments_covered')
    amount_allocated = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,
                                           help_text="Amount from this payment specifically allocated to this member's account.")
    notes = models.TextField(blank=True, null=True, help_text="Specific notes for this member's coverage in this payment.")

    class Meta:
        unique_together = ('payment', 'individual') # A member can only be covered once per payment
        verbose_name = "Covered Member"
        verbose_name_plural = "Covered Members"

    def __str__(self):
        return f"{self.individual.full_name} covered by OR #{self.payment.receipt_number}"

    def save(self, *args, **kwargs):
        # Ensure that the amount allocated does not exceed the total payment amount
        # This check should ideally be done in form validation, but added here for safety.
        if self.amount_allocated > self.payment.amount:
            # You might want to raise a ValidationError or adjust the amount
            # For now, let's just log or set it to the max if it somehow gets here
            print(f"Warning: Amount allocated {self.amount_allocated} for {self.individual.full_name} exceeds payment total {self.payment.amount}.")
            # self.amount_allocated = self.payment.amount # Example: Cap it if it exceeds

        super().save(*args, **kwargs)