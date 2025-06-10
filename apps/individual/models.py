# apps/individual/models.py
from django.db import models
# Fixed: Changed direct import to string reference for ForeignKey to avoid circular import
# from apps.family.models import Family 

# Choices for Sex field
GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
]

# Choices for Civil Status field
CIVIL_STATUS_CHOICES = [
    ('S', 'Single'),
    ('M', 'Married'),
    ('W', 'Widowed'),
    ('D', 'Divorced'),
    ('P', 'Separated'), # For "Pakasal" (Separated)
]

class Individual(models.Model):
    # Personal Information
    surname = models.CharField(max_length=100)
    given_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    suffix_name = models.CharField(max_length=10, blank=True, null=True) # Ito ang field na hinahanap

    sex = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        default='M', 
        help_text="The biological sex of the individual."
    )
    
    civil_status = models.CharField(
        max_length=1,
        choices=CIVIL_STATUS_CHOICES,
        default='S', 
        help_text="The civil status of the individual."
    )

    birth_date = models.DateField(blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    email_address = models.EmailField(max_length=255, blank=True, null=True)
    
    # Membership Information
    # Fixed: Changed to string reference 'family.Family'
    family = models.ForeignKey('family.Family', on_delete=models.SET_NULL, null=True, blank=True)
    is_active_member = models.BooleanField(default=True)
    is_alive = models.BooleanField(default=True) 
    
    RELATIONSHIP_CHOICES = [
        ('HEAD', 'Head of Family'),
        ('SPOUSE', 'Spouse'),
        ('CHILD', 'Child'),
        ('PARENT', 'Parent'),
        ('OTHER', 'Other Relative'),
    ]
    relationship = models.CharField(
        max_length=10,
        choices=RELATIONSHIP_CHOICES,
        default='CHILD',
        help_text="Relationship to the head of the family."
    )

    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.surname}, {self.given_name}"

    class Meta:
        verbose_name_plural = "Individuals"
