# apps/family/models.py
from django.db import models
from apps.church.models import Church
# Dili na nato kailangan ang apps.individual.models diri
# kay ang ForeignKey kay string reference na lang
# from apps.individual.models import Individual


class Family(models.Model):
    church = models.ForeignKey(
        Church, on_delete=models.CASCADE, related_name='families')
    family_name = models.CharField(max_length=255)
    address = models.TextField()
    is_active = models.BooleanField(default=True)
    contact_number = models.CharField(
        max_length=20, blank=True, null=True)  # Confirmed: Naa ni nga field

    # GI-FIX: Gibalik ang ngalan sa field ngadto sa 'head_of_family'
    head_of_family = models.ForeignKey(
        # Gamit gihapon ang string reference para walay circular import
        'individual.Individual',
        on_delete=models.SET_NULL,
        null=True,                 # Gitugotan nga NULL sa database
        blank=True,                # Gitugotan nga blank sa forms
        # Para dali makuha ang mga pamilya nga gi-head sa usa ka individual
        related_name='headed_families',
        help_text="Ang pangunang indibidwal nga nagrepresentar sa pamilya (optional)"
    )

    class Meta:
        verbose_name_plural = "Families"
        ordering = ['family_name']

    def __str__(self):
        return self.family_name
