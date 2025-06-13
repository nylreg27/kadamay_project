# apps/payment/models.py

from django.db import models
from apps.individual.models import Individual  # Assuming this path
from apps.church.models import Church  # Assuming this path
# Add other imports if needed, e.g., from apps.family.models import Family
from django.utils import timezone


class ContributionType(models.Model):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Payment(models.Model):
    # Payee: The individual who made the payment
    individual = models.ForeignKey(Individual, on_delete=models.PROTECT,
                                   related_name='payments_made',
                                   verbose_name="Payee")

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

    receipt_no = models.CharField(
        max_length=50, unique=True, blank=True, null=True)
    notes = models.TextField(blank=True, null=True,
                             verbose_name="Remarks")  # Use for Remarks

    # Covered Members: Individuals covered by this payment (ManyToMany)
    covered_members = models.ManyToManyField(Individual, related_name='payments_covered', blank=True,
                                             help_text="Select members covered by this payment.")

    # Optional: If "Share For" is a specific individual other than the payee
    # share_for_individual = models.ForeignKey(Individual, on_delete=models.SET_NULL,
    #                                           related_name='payments_shared_for',
    #                                           blank=True, null=True,
    #                                           verbose_name="Share For Individual")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True) # If you have User model

    class Meta:
        ordering = ['-date_paid', '-created_at']
        verbose_name = "Payment/Contribution"
        verbose_name_plural = "Payment/Contributions"

    def __str__(self):
        return f"{self.individual.full_name} - {self.contribution_type.name} ({self.amount})"
