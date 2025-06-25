# apps/account/models.py (Corrected Version)

from django.db import models
from django.contrib.auth import get_user_model

# Import Church model. It's okay to import it directly now,
# as long as Church app is in INSTALLED_APPS before account.
# If you prefer string reference 'church.Church', that's also fine for circular import safety.
from apps.church.models import Church

User = get_user_model() # Get the currently active user model

class Profile(models.Model):
    """
    User profile to extend Django's built-in User model.
    Contains additional personal information and custom settings.
    """
    # User roles (used in StyledUserCreationForm and potentially for permissions)
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

    # Theme choices for user interface
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

    # Linking to Django's built-in User model
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Custom fields for Profile
    contact_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Contact Number")
    address = models.TextField(blank=True, null=True, verbose_name="Address")
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="Date of Birth")
    
    # User role (separate from Django Groups, but often synced or used for display)
    role = models.CharField(max_length=20, choices=USER_ROLES, default=USER, verbose_name="User Role")
    
    # User-selected theme
    theme = models.CharField(max_length=50, choices=THEME_CHOICES, default='corporate', verbose_name="Theme")
    
    # Profile picture
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True, verbose_name="Profile Picture")
    
    # Link to Church model (User's primary church assignment)
    # This assumes 'Church' model will exist in 'apps.church'
    church_assignment = models.ForeignKey(
        Church, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_profiles', verbose_name="Assigned Church"
    )
    
    # General active status for the profile
    is_active = models.BooleanField(default=True, verbose_name="Is Profile Active?")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_role_display(self):
        # Returns the human-readable role name
        return dict(self.USER_ROLES).get(self.role, self.role)

    def __str__(self):
        return f"{self.user.username}'s Profile ({self.get_role_display()})"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering = ['user__username'] # Order profiles by username


# UserChurch model (if you need a separate many-to-many like assignment or specific role in church)
# Your previous UserChurch had OneToOneField, which limits a user to only one church assignment.
# If a user can be affiliated with multiple churches, it should be ManyToMany.
# For simplicity and given 'church_assignment' in Profile, this might be redundant unless it has distinct purpose.
# If its purpose is to show one main church assignment, then ForeignKey in Profile is enough.
# Let's keep it for now as it was explicitly defined by you with OneToOne, assuming a specific use case
# like a 'primary' church assignment. If a user can only ever be linked to one church at a time,
# then `church_assignment` in Profile is enough, and this model can be removed.
# For now, I'm keeping it as a OneToOne as per your provided code, but be aware of its implications.

class UserChurch(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='assigned_church_link',
        verbose_name="User"
    )
    church = models.ForeignKey(
        Church, on_delete=models.CASCADE, related_name='assigned_users_via_link',
        verbose_name="Assigned Church"
    )
    
    # Example: If this model's purpose is to define a specific role *within* a church context
    # role_in_church = models.CharField(max_length=50, blank=True, null=True, verbose_name="Role in Church")

    class Meta:
        verbose_name = 'User Church Assignment'
        verbose_name_plural = 'User Church Assignments'
        unique_together = ('user', 'church') # A user can only be assigned to a specific church once via this link
        ordering = ['user__username', 'church__name']

    def __str__(self):
        return f"{self.user.username} assigned to {self.church.name}"

