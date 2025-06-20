# apps/contribution_type/models.py
from django.db import models


class ContributionType(models.Model):
    """
    Model to define different types of contributions (e.g., Monthly Dues, Special Offering).
    """
    name = models.CharField(max_length=100, unique=True,
                            help_text="Name of the contribution type (e.g., 'Monthly Dues')")
    description = models.TextField(blank=True, null=True,
                                   help_text="Detailed description of this contribution type")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contribution Type"
        verbose_name_plural = "Contribution Types"
        ordering = ['name']  # Order by name alphabetically

    def __str__(self):
        return self.name
