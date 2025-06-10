from django.db import models
from apps.individual.models import Individual

class ContributionType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = 'Contribution Type'
        verbose_name_plural = 'Contribution Types'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Payment(models.Model):
    individual = models.ForeignKey(Individual, on_delete=models.CASCADE, related_name='payments')
    contribution_type = models.ForeignKey(ContributionType, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_paid = models.DateField()
    remarks = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-date_paid']
    
    def __str__(self):
        return f"{self.individual} - {self.contribution_type} - {self.date_paid}"