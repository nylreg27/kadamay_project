# apps/account/models.py
from django.db import models
from django.contrib.auth import get_user_model # Always use get_user_model() for custom User references
from apps.church.models import Church # Keep this for UserChurch model
# from django.urls import reverse_lazy # Not used directly in models.py

User = get_user_model()

# Listahan ng mga available na DaisyUI themes
DAISYUI_THEMES = [
    ('light', 'Light'),
    ('dark', 'Dark'),
    ('corporate', 'Corporate'),
    ('cupcake', 'Cupcake'),
    ('bumblebee', 'Bumblebee'),
    ('emerald', 'Emerald'),
    ('synthwave', 'Synthwave'),
    ('retro', 'Retro'),
    ('garden', 'Garden'),
    ('business', 'Business'),
    ('night', 'Night'),
]

# UserChurch model (This looks correct as a standalone model)
class UserChurch(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='assigned_church')
    church = models.ForeignKey(
        Church, on_delete=models.CASCADE, related_name='assigned_users')

    @property
    def role(self):
        # This property will determine the user's role based on superuser status
        if self.user.is_superuser:
            return "Admin"
        # You might want to add more roles here later based on groups or other fields
        return "Member"

    class Meta:
        verbose_name = 'User Church Assignment'
        verbose_name_plural = 'User Church Assignments'
        unique_together = ('user', 'church') # Ensures a user can only be assigned to one church at a time in this context

    def __str__(self):
        return f"{self.user.username} - {self.church.name}"

# Profile model (CORRECTLY UN-INDENTED and UPDATED fields)
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile') # Added related_name
    
    # Updated fields based on our theme and profile picture features
    theme = models.CharField(
        max_length=50,
        choices=DAISYUI_THEMES,
        default='corporate', # Default theme for new users
        blank=True,
        null=True,
        help_text="Choose your preferred color theme for the application."
    )
    profile_picture = models.ImageField(
        upload_to='profile_pics/', # Files will be saved in MEDIA_ROOT/profile_pics/
        blank=True,
        null=True,
        help_text="Upload your profile picture (optional)."
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"

