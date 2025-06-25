# apps/account/admin.py (Final Fix for List Filter / Search Issue)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Profile, UserChurch # Import both models

# --- IMPORTANT: Unregister the default User model first! ---
# This prevents the 'AlreadyRegistered' error.
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass # If it's not registered (e.g., in tests), just continue

# Inline for Profile model (to display Profile fields directly in User admin)
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user' # Specifies the foreign key on the Profile model that links to User

# Custom User Admin to include Profile inline and UserChurch details
class CustomUserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'is_active', 'is_staff', 'is_superuser',
        'get_profile_role',
        'get_assigned_church', # Display custom method for assigned church
    )

    list_filter = (
        'is_active', 'is_staff', 'is_superuser', 'groups',
        'profile__role',
        # --- FIX: Use 'assigned_church_link' as per your UserChurch model's related_name ---
        'assigned_church_link__church', # Filter by Church assigned via UserChurch
    )

    search_fields = (
        'username', 'first_name', 'last_name', 'email',
        'profile__role',
        # --- FIX: Use 'assigned_church_link' as per your UserChurch model's related_name ---
        'assigned_church_link__church__name', # Search by Church Name assigned via UserChurch
    )

    # Custom method to get the role from the associated Profile
    def get_profile_role(self, obj):
        return obj.profile.get_role_display() if hasattr(obj, 'profile') else 'N/A'
    get_profile_role.short_description = 'Profile Role' # Column header in admin

    # Custom method to get the assigned church from UserChurch
    def get_assigned_church(self, obj):
        # Since UserChurch uses OneToOneField with related_name='assigned_church_link'
        # we can directly access it via obj.assigned_church_link
        if hasattr(obj, 'assigned_church_link') and obj.assigned_church_link:
            return obj.assigned_church_link.church.name
        return 'N/A'
    get_assigned_church.short_description = 'Assigned Church' # Column header in admin

# Register custom User admin explicitly
admin.site.register(User, CustomUserAdmin)


# Admin for the UserChurch model itself
@admin.register(UserChurch)
class UserChurchAdmin(admin.ModelAdmin):
    list_display = ('user', 'church',)
    list_filter = ('church',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'church__name')
    autocomplete_fields = ('user', 'church')

