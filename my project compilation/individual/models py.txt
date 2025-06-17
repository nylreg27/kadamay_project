# apps/individual/models.py

from django.db import models
# Assuming Family model exists in apps.family.models
from apps.family.models import Family 

GENDER_CHOICES = [
    ('MALE', 'Male'),
    ('FEMALE', 'Female')
]

CIVIL_STATUS_CHOICES = [
    ('SINGLE', 'Single'),
    ('MARRIED', 'Married'),
    ('DIVORCED', 'Divorced'),
    ('WIDOWED', 'Widowed'),
    ('SEPARATED', 'Separated'),
]

# Assuming your Church model is defined somewhere, e.g., apps.church.models
# from apps.church.models import Church

class Individual(models.Model):
    given_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    surname = models.CharField(max_length=100)
    suffix_name = models.CharField(max_length=10, blank=True, null=True)

    sex = models.CharField(
        max_length=50, choices=GENDER_CHOICES, blank=True, null=True)
    civil_status = models.CharField(
        max_length=150, choices=CIVIL_STATUS_CHOICES, blank=True, null=True)

    birth_date = models.DateField(blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    email_address = models.EmailField(blank=True, null=True)

    membership_id = models.CharField(max_length=50, blank=True, null=True)

    address = models.CharField(max_length=255, blank=True, null=True) # If this is a CharField

    RELATIONSHIP_CHOICES = [
        ('HEAD', 'Head'),
        ('SPOUSE', 'Spouse'),
        ('CHILD', 'Child'),
        ('PARENT', 'Parent'),
        ('SIBLING', 'Sibling'),
        ('OTHER', 'Other'),
    ]
    relationship = models.CharField(
        max_length=10, choices=RELATIONSHIP_CHOICES)

    MEMBERSHIP_STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('PENDING', 'Pending'),
    ]
    membership_status = models.CharField(
        max_length=150, choices=MEMBERSHIP_STATUS_CHOICES, default='ACTIVE')

    is_active_member = models.BooleanField(default=True)
    is_alive = models.BooleanField(default=True)

    date_added = models.DateTimeField(auto_now_add=True)

    family = models.ForeignKey(
        Family, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    
    # You might have a religion or occupation field that was not in the provided snippet
    # religion = models.CharField(max_length=100, blank=True, null=True)
    # occupation = models.CharField(max_length=100, blank=True, null=True)
    # tin = models.CharField(max_length=20, blank=True, null=True)

    @property
    def full_name(self):
        parts = []
        if self.given_name:
            parts.append(self.given_name)
        if self.middle_name:
            parts.append(self.middle_name)
        if self.surname:
            parts.append(self.surname)
        if self.suffix_name:
            parts.append(self.suffix_name)
        return " ".join(parts).strip()

    def get_sex_display(self):
        return dict(GENDER_CHOICES).get(self.sex)

    def get_civil_status_display(self):
        return dict(CIVIL_STATUS_CHOICES).get(self.civil_status)

    def get_relationship_display_value(self):
        return dict(self.RELATIONSHIP_CHOICES).get(self.relationship, self.relationship)

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name_plural = "Individuals"

