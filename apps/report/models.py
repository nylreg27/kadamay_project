from django.db import models
from django.contrib.auth.models import User
from apps.church.models import Church

class ReportLog(models.Model):
    REPORT_TYPE_CHOICES = [
        ('member_list', 'Member List'),
        ('contribution', 'Contribution Report'),
        ('family', 'Family Report'),
        ('deceased', 'Deceased Members'),
        ('inactive', 'Inactive Members'),
        ('custom', 'Custom Report')
    ]
    
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    church = models.ForeignKey(Church, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Report Log'
        verbose_name_plural = 'Report Logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"