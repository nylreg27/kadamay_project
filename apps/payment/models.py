# apps/payment/models.py

from django.db import models
from django.conf import settings  # Para sa AUTH_USER_MODEL
# Para sa auto_now_add, auto_now, default values
from django.utils import timezone
from apps.individual.models import Individual
# Kung ang UserChurch ug Profile naa sa 'apps/account/models.py', husto kini.
from apps.account.models import UserChurch, Profile
# Kung ang ContributionType naa sa 'apps/contribution_type/models.py', husto kini.
from apps.contribution_type.models import ContributionType


class Payment(models.Model):
    """
    Model para sa matag payment transaction sa KADAMAY.
    """
    permissions = [
        ("can_validate_payment", "Can validate payments (for InCharge/Admin)"),
        ("can_create_payment", "Can create new payments (for Cashier/InCharge/Admin)"),
        ("can_cancel_payment", "Can cancel payments (for Auditor/Admin)"),
        ("view_payment", "Can view payment records"),
    ]

    # OR Number - Automatic na mag-generate, unique, dili editable
    or_number = models.CharField(
        max_length=20, unique=True, db_index=True, verbose_name="OR Number")

    # Kinsa ang nagbayad (payer) - ForeignKey sa Individual model
    individual = models.ForeignKey(
        Individual,
        # Kung ma-delete ang Individual, ma-NULL lang ang field, dili ma-delete ang Payment
        on_delete=models.SET_NULL,
        related_name='payments_made',
        null=True,
        blank=True,
        verbose_name="Nagbayad (Payer)"
    )

    # Kantidad sa gibayad
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Kantidad")

    # Petsa sa pagbayad
    date_paid = models.DateField(
        default=timezone.now, verbose_name="Petsa sa Bayad")

    # Pamaagi sa pagbayad
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('gcash', 'GCash'),
        # Add more methods if needed, e.g., ('bank_transfer', 'Bank Transfer')
    ]
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash',
        verbose_name="Pamaagi sa Bayad"
    )

    # Reference number sa Gcash (kung gcash ang pamaagi)
    gcash_reference_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="GCash Reference Number",
        help_text="Required if Payment Method is GCash and needs validation."
    )

    # Status sa Payment
    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('pending', 'Pending (for GCash validation)'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default='paid',
        verbose_name="Status sa Bayad"
    )

    # Type sa Kontribusyon (e.g., Monthly Dues, Special Fund)
    contribution_type = models.ForeignKey(
        ContributionType,
        # Kung ma-delete ang ContributionType, ma-NULL lang ang field
        on_delete=models.SET_NULL,
        related_name='payments',
        null=True,
        blank=True,
        verbose_name="Tipo sa Kontribusyon"
    )

    # Kinsa ang nagkolekta sa bayad (usually ang nag-create sa record)
    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='payments_collected',
        null=True,
        blank=True,
        verbose_name="Gikolekta ni"
    )

    # Kung naay mag-validate (e.g., sa Gcash payments)
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='payments_validated',
        null=True,
        blank=True,
        verbose_name="Gi-validate ni"
    )
    validated_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Petsa sa Pag-validate")

    # Kung naay mag-cancel sa payment
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='payments_cancelled',
        null=True,
        blank=True,
        verbose_name="Gi-kansela ni"
    )
    cancelled_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Petsa sa Pag-kansela")
    cancellation_reason = models.TextField(
        null=True, blank=True, verbose_name="Rason sa Pagkansela")

    # Audit fields
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Gihimo niadtong")
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Gi-update niadtong")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='payments_created',
        null=True,
        blank=True,
        verbose_name="Gihimo ni"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='payments_updated',
        null=True,
        blank=True,
        verbose_name="Gi-update ni"
    )

    class Meta:
        verbose_name = "Bayad"
        verbose_name_plural = "Mga Bayad"
        # Mag-order based sa petsa, unya OR number
        ordering = ['-date_paid', '-or_number']

    def __str__(self):
        return f"OR #{self.or_number} - {self.individual.first_name if self.individual else 'N/A'} - {self.amount}"

    def save(self, *args, **kwargs):
        # Example: Ensure only 'pending' Gcash payments have reference number.
        if self.payment_method != 'gcash' and self.status != 'pending':
            self.gcash_reference_number = None
        super().save(*args, **kwargs)


class CoveredMember(models.Model):
    """
    Model para sa mga miyembro sa pamilya nga gi-cover sa usa ka Payment.
    """
    payment = models.ForeignKey(
        Payment,
        # Kung ma-delete ang Payment, ma-delete pud ang CoveredMember records
        on_delete=models.CASCADE,
        related_name='covered_members',
        verbose_name="Bayad"
    )
    individual = models.ForeignKey(
        Individual,
        # Kung ma-delete ang Individual, ma-delete pud ang CoveredMember record (consider SET_NULL instead if you want to keep payment record)
        on_delete=models.CASCADE,
        related_name='covered_payments',
        verbose_name="Miyembro nga Gi-cover"
    )
    amount_covered = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Kantidad nga Gi-cover")
    # Pwede nimo butangan og 'notes' field here kung gusto nimo mag-add og remarks per covered member.

    class Meta:
        verbose_name = "Miyembro nga Gi-cover"
        verbose_name_plural = "Mga Miyembro nga Gi-cover"
        # Siguraduhin nga ang usa ka Individual dili ma-cover sa parehas nga Payment labaw sa kausa
        unique_together = ('payment', 'individual')

    def __str__(self):
        return f"{self.individual.first_name if self.individual else 'N/A'} (for OR #{self.payment.or_number})"
