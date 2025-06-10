from django.db import models
from django.contrib.auth import get_user_model
from apps.church.models import Church 
User = get_user_model()


class InChargeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    church = models.ForeignKey(Church, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.church.name}"


class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    church = models.ForeignKey(Church, on_delete=models.CASCADE, related_name='chat_messages')
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.sender.username} - {self.sent_at.strftime('%Y-%m-%d %H:%M')}"
