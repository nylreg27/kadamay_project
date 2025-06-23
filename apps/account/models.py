# apps/account/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.church.models import Church  # Import ng Church model mo

# Custom User model
User = get_user_model()


class Profile(models.Model):
   # Choices for user roles
    ADMIN = 'ADMIN'
    CASHIER = 'CASHIER'
    IN_CHARGE = 'IN_CHARGE'
    USER = 'USER'  # Standard user without special payment access

    USER_ROLES = [
        (ADMIN, 'Admin'),
        (CASHIER, 'Cashier'),
        (IN_CHARGE, 'In-Charge'),
        (USER, 'User'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Default role is 'USER'
    role = models.CharField(max_length=20, choices=USER_ROLES, default=USER)
    profile_picture = models.ImageField(
        upload_to='profile_pics/', blank=True, null=True)

    def get_role_display(self):
        # Returns the human-readable role name
        return dict(self.USER_ROLES).get(self.role, self.role)

    def __str__(self):
        return f"{self.user.username}'s Profile ({self.get_role_display()})"

    # Inilipat ang THEME_CHOICES sa loob ng Profile class
    THEME_CHOICES = [
        ('light', 'Light (Default DaisyUI)'),
        ('dark', 'Dark'),
        ('corporate', 'Corporate'),  # Your current default
        ('retro', 'Retro'),
        ('cyberpunk', 'Cyberpunk'),
        ('valentine', 'Valentine'),
        ('halloween', 'Halloween'),
        ('forest', 'Forest'),
        ('aqua', 'Aqua'),
        ('luxury', 'Luxury'),
        ('dracula', 'Dracula'),
        ('cmyk', 'CMYK'),
        ('autumn', 'Autumn'),
        ('business', 'Business'),
        ('acid', 'Acid'),
        ('lemonade', 'Lemonade'),
        ('night', 'Night'),
        ('coffee', 'Coffee'),
        ('winter', 'Winter'),
        ('dim', 'Dim'),
        ('nord', 'Nord'),
        ('sunset', 'Sunset'),
    ]
    theme = models.CharField(
        max_length=50, choices=THEME_CHOICES, default='corporate')
    profile_picture = models.ImageField(
        upload_to='profile_pics/', blank=True, null=True)

    # Maaari kang magdagdag ng iba pang fields dito para sa user profile

    def __str__(self):
        return self.user.username

# Signal para automatic na gumawa ng Profile kapag may bagong User, at i-save ang existing profile


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()


class UserChurch(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='assigned_church')
    church = models.ForeignKey(
        Church, on_delete=models.CASCADE, related_name='assigned_users')

    @property
    def role(self):
        if self.user.is_superuser:
            return "Admin"
        # You might want to add more roles here later based on groups or other fields
        return "Member"

    class Meta:
        verbose_name = 'User Church Assignment'
        verbose_name_plural = 'User Church Assignments'
        unique_together = ('user', 'church')

    def __str__(self):
        return f"{self.user.username} - {self.church.name}"
