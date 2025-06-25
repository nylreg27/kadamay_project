# apps/account/signals.py (Corrected Version)

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Signal handler to create or update a Profile instance whenever a User is saved.
    """
    if created:
        # Create a new Profile if the User is new
        Profile.objects.create(user=instance)
    else:
        # If User exists, ensure its associated Profile is also saved
        # This handles cases where User fields are updated via Django's admin or other forms
        # and ensures the profile fields are kept in sync or simply saved.
        # The 'try-except' handles cases where a Profile might not exist for an old User record
        # (though our create on signal should prevent this for new users).
        try:
            instance.profile.save()
        except Profile.DoesNotExist:
            # If for some reason a Profile doesn't exist for an old user, create one.
            # This is a fallback for legacy data or unexpected scenarios.
            Profile.objects.create(user=instance)

