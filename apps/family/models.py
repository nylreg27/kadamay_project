# apps/family/models.py (Corrected)

from django.db import models
from django.contrib.auth import get_user_model
from apps.church.models import Church
# Keep this import, it's needed for head_of_family and Individual uses 'family.Family' string
from apps.individual.models import Individual

User = get_user_model() # Makuha ang User model sa Django

class Family(models.Model):
    # FIXED: Renamed 'name' to 'family_name' to match what your form expects
    family_name = models.CharField(max_length=255, verbose_name="Family Name", unique=True)
    address = models.TextField(blank=True, null=True, verbose_name="Family Address")
    church = models.ForeignKey(Church, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='families', verbose_name="Associated Church")
    head_of_family = models.ForeignKey(
        Individual,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_families',
        verbose_name="Head of Family"
    )

    # ADDED: These fields were missing but expected by the FamilyForm
    contact_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Contact Number")
    is_active = models.BooleanField(default=True, verbose_name="Is Active?")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Family"
        verbose_name_plural = "Families"
        # FIXED: Changed ordering to 'family_name'
        ordering = ['family_name']

    def __str__(self):
        # FIXED: Changed from self.name to self.family_name
        return self.family_name

class FamilyMember(models.Model):
    RELATIONSHIP_CHOICES = [
        ('HEAD', 'Head of Household'),
        ('SPOUSE', 'Spouse'),
        ('CHILD', 'Child'),
        ('PARENT', 'Parent'),
        ('SIBLING', 'Sibling'),
        ('OTHER', 'Other Relative'),
    ]

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='memberships', verbose_name="Family Group")
    # This is correct with the string reference 'individual.Individual'
    individual = models.ForeignKey('individual.Individual', on_delete=models.CASCADE, related_name='familymembership', verbose_name="Individual Member")
    relationship = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_CHOICES,
        default='OTHER',
        verbose_name="Relationship to Head"
    )

    date_added = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='family_members_added')
    is_active = models.BooleanField(default=True, verbose_name="Is Active Member")

    class Meta:
        verbose_name = "Family Member"
        verbose_name_plural = "Family Members"
        unique_together = ('family', 'individual')
        # FIXED: Changed ordering to 'family__family_name'
        ordering = ['family__family_name', 'individual__surname', 'individual__given_name']

    def __str__(self):
        try:
            individual_obj = self.individual
            if hasattr(individual_obj, 'full_name'):
                return f"{individual_obj.full_name} ({self.get_relationship_display()}) in {self.family.family_name}"
            return f"{individual_obj.given_name} {individual_obj.surname} ({self.get_relationship_display()}) in {self.family.family_name}"
        except Exception:
            return f"Family Member {self.id} in {self.family.family_name}"