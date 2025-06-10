from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class IssueReport(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=50, choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')])
    status = models.CharField(max_length=50, choices=[('Open', 'Open'), ('In Progress', 'In Progress'), ('Closed', 'Closed')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
