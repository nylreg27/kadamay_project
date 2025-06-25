# apps/payment/models.py (Corrected Version)

from django.db import models
from django.contrib.auth import get_user_model
from apps.church.models import Church # Import Church model - assuming still needed for other models in the future, or delete if not.
# No direct import of Individual or ContributionType here due to string references.

User = get_user_model() # Get the currently active user model

class Payment(models.Model):
    """
    Model for recording payments from KADAMAY members.
    Handles multiple payments under one OR number via PaymentCoveredMember.
    """
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('GCASH', 'G-Cash'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled'),
    ]

    # FIELD ADDED/MODIFIED FOR CONSISTENCY WITH FORMS.PY AND REQUIREMENTS
    individual = models.ForeignKey(
        'individual.Individual',  # String reference to Individual model
        on_delete=models.CASCADE,
        related_name='payments_as_payer',
        verbose_name="Payer"
    )

    # RENAMED from 'total_amount' to 'amount' for consistency with forms.py
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Amount Paid")
    
    # RENAMED from 'payment_date' to 'date_paid' and changed to DateField
    # Removed auto_now_add=True so it can be set by the form
    date_paid = models.DateField(verbose_name="Date Paid")
    
    # NEW FIELD: contribution_type, needed for the PaymentForm
    contribution_type = models.ForeignKey(
        'contribution_type.ContributionType',  # String reference to ContributionType model
        on_delete=models.SET_NULL, # Set to null if the ContributionType is deleted
        null=True, blank=True,
        related_name='payments_by_type',
        verbose_name="Contribution Type"
    )

    or_number = models.CharField(max_length=50, unique=True, verbose_name="Official Receipt Number")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, verbose_name="Payment Method")
    
    # For G-Cash payments
    gcash_reference_number = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="G-Cash Reference No."
    )
    is_validated = models.BooleanField(default=False, verbose_name="Is G-Cash Validated?")
    validated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='payments_validated', verbose_name="Validated By"
    )

    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='PAID', verbose_name="Payment Status")
    collected_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='payments_collected', verbose_name="Collected By"
    )
    remarks = models.TextField(blank=True, null=True, verbose_name="Remarks/Notes")

    created_at = models.DateTimeField(auto_now_add=True) # This is for tracking when the record was created
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        # Updated ordering to use 'date_paid'
        ordering = ['-date_paid', 'or_number'] 

    def __str__(self):
        # Using 'amount' now
        return f"OR #{self.or_number} - {self.amount} ({self.get_payment_method_display()})"

    def save(self, *args, **kwargs):
        # Auto-generate OR number if not set (or is empty string)
        if not self.or_number:
            last_payment = Payment.objects.order_by('-or_number').first()
            if last_payment and last_payment.or_number.isdigit():
                # Assuming OR numbers are purely numeric like 2000134
                next_or_number = int(last_payment.or_number) + 1
            else:
                next_or_number = 2000001 # Starting OR number for KADAMAY project
            self.or_number = str(next_or_number)
        super().save(*args, **kwargs)

class PaymentCoveredMember(models.Model):
    """
    Represents an individual covered by a specific Payment,
    allowing multiple individuals per Payment and tracking their attributed amount.
    """
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='covered_members', verbose_name="Payment")
    # Gamiton ang string reference para sa 'Individual' model para walay circular import
    individual = models.ForeignKey('individual.Individual', on_delete=models.CASCADE, related_name='payments_covered', verbose_name="Covered Individual")
    amount_covered = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Amount Covered for Individual")
    remarks = models.TextField(blank=True, null=True, verbose_name="Remarks for this Individual")

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='covered_members_created', verbose_name="Added By"
    )

    class Meta:
        verbose_name = "Payment Covered Member"
        verbose_name_plural = "Payment Covered Members"
        # Ensure an individual is only covered once per payment
        unique_together = ('payment', 'individual')
        ordering = ['payment__or_number', 'individual__surname']

    def __str__(self):
        # Access Individual properties through the relationship
        individual_name = "Unknown Individual"
        if self.individual:
            try:
                # Ensure Individual model has 'full_name' property
                if hasattr(self.individual, 'full_name'):
                    individual_name = self.individual.full_name
                else:
                    individual_name = f"{self.individual.first_name} {self.individual.surname}"
            except Exception:
                pass # If Individual object cannot be retrieved or has no name

        return f"Payment OR#{self.payment.or_number} for {individual_name} - {self.amount_covered}"