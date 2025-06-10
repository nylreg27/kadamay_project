# apps/church/models.py
from django.db import models
from django.contrib.auth import get_user_model # Kung ang User model ay ginagamit for in_charge

User = get_user_model() # Default Django User model

class District(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Church(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    # FIXED: Tinanggal ang date_created field
    # date_created = models.DateTimeField(auto_now_add=True) 

    in_charge = models.ForeignKey(
        User, # Assuming User model ang in_charge
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='churches_managed'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Churches" # Para sa admin panel

