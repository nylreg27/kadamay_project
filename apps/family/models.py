# apps/family/models.py
from django.db import models
from apps.church.models import Church 
# FIXED: Changed direct import to string reference for ForeignKey to avoid circular import
# from apps.individual.models import Individual 

class Family(models.Model):
    family_name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    # Church field
    church = models.ForeignKey(
        Church,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='families' 
    )

    # In_charge field - kailangan ng unique related_name
    # FIXED: Changed to string reference 'individual.Individual'
    in_charge = models.ForeignKey(
        'individual.Individual', # Assuming Individual model ang in_charge
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='families_managed' 
    )

    def __str__(self):
        return self.family_name

