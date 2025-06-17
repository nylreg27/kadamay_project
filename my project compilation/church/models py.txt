# apps/church/models.py (Full and Corrected Version)

from django.db import models
# Kung ang User model ay ginagamit for in_charge
from django.contrib.auth import get_user_model

User = get_user_model()  # Default Django User model


class District(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Church(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    district = models.ForeignKey(
        District, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    in_charge = models.ForeignKey(
        User,  # Assuming User model ang in_charge
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='churches_managed'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Churches"  # Para sa admin panel
