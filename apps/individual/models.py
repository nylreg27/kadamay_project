# apps/individual/models.py

from django.db import models
from apps.family.models import Family
from django.utils import timezone
from decimal import Decimal

# Import Church model (assuming Individual has a ForeignKey to Church)
from apps.church.models import Church


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

    # FIXED: Membership ID is now unique and required (blank=False, null=False)
    membership_id = models.CharField(
        max_length=50, unique=True, blank=False, null=False)
    # Since you have run the backfill command, all existing records should now have an ID.
    # So, it's safe to set blank=False, null=False.

    address = models.CharField(max_length=255, blank=True, null=True)

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

    church = models.ForeignKey(
        Church, on_delete=models.SET_NULL, null=True, blank=True, related_name='individuals'
    )

    # Custom save method to auto-generate membership_id

    def save(self, *args, **kwargs):
        # Only generate a new membership_id if it's not already set
        if not self.membership_id:
            today = timezone.localdate()  # Get current date in local timezone

            # Format the date part (YYMMDD)
            # e.g., '250619' for June 19, 2025
            date_part = today.strftime('%y%m%d')

            # Find the last membership_id for today's date
            # We need to filter by IDs that start with the current date part
            # and then order by the ID in descending order to get the latest one.
            # Using __startswith for efficient lookup if you have many records.
            last_individual_for_today = Individual.objects.filter(
                # Filter IDs like '250619-'
                membership_id__startswith=f"{date_part}-"
                # Get the highest sequence number
            ).order_by('-membership_id').first()

            new_sequence = 1
            if last_individual_for_today:
                # Extract the numeric sequence part from the last ID
                # e.g., if last ID is '250619-0012', we get '0012'
                last_id_sequence_str = last_individual_for_today.membership_id.split(
                    '-')[-1]
                try:
                    last_sequence = int(last_id_sequence_str)
                    new_sequence = last_sequence + 1
                except ValueError:
                    # Fallback if the sequence part is not a valid number (shouldn't happen with proper IDs)
                    new_sequence = 1  # Reset to 1 if parsing fails unexpectedly

            # Format the new membership ID: YYMMDD-XXXX (e.g., 250619-0001)
            # Use zfill(4) to ensure it's always 4 digits, padding with leading zeros
            self.membership_id = f"{date_part}-{str(new_sequence).zfill(4)}"

        # Call the original save method to save the instance to the database
        super().save(*args, **kwargs)

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
