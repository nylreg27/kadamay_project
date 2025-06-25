# apps/account/forms.py (Corrected Version)

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Profile # Import Profile model

User = get_user_model()

class StyledUserCreationForm(UserCreationForm):
    """
    Custom User Creation Form with additional fields for User and Profile,
    and consistent DaisyUI/Tailwind styling.
    """
    email = forms.EmailField(
        label='EMAIL ADDRESS',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'input input-bordered w-full uppercase focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs',
            'placeholder': 'Enter email address'
        })
    )

    # Role field from Profile model choices
    role = forms.ChoiceField(
        choices=Profile.USER_ROLES, # Use choices from the consolidated Profile model
        label='ROLE',
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full uppercase focus:outline-none focus:ring-2 focus:ring-primary select-xs text-xs'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        # Include 'email', 'first_name', 'last_name' from User model
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply consistent styling to all fields
        for field_name, field in self.fields.items():
            if field_name not in ['role', 'is_active', 'is_staff', 'is_superuser']:
                # Apply input styling for text-based fields (username, email, passwords, names)
                field.widget.attrs.update({
                    'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs'
                })
            elif field_name in ['is_active', 'is_staff', 'is_superuser']:
                # Apply checkbox styling
                field.widget.attrs.update(
                    {'class': 'checkbox checkbox-primary'})
            elif field_name == 'role':
                # Apply select styling, already defined in the field itself
                pass # Already handled by specific widget above

        # Set placeholders
        if 'username' in self.fields:
            self.fields['username'].widget.attrs['placeholder'] = 'Choose a username'
        if 'first_name' in self.fields:
            self.fields['first_name'].widget.attrs['placeholder'] = 'Enter first name'
        if 'last_name' in self.fields:
            self.fields['last_name'].widget.attrs['placeholder'] = 'Enter last name'
        # 'email' placeholder is already set in its definition above.

    def save(self, commit=True):
        # Save the User instance
        user = super().save(commit=commit)
        if commit:
            # Create or get the Profile for the new user and set the role
            # The signal (apps/account/signals.py) already creates the profile.
            # Here we just ensure the role is set if the profile already exists from signal.
            profile = user.profile # Access the profile created by the signal
            profile.role = self.cleaned_data['role']
            profile.save()
        return user

class UserLoginForm(AuthenticationForm):
    """
    Login form with DaisyUI/Tailwind styling.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply styling to username and password fields
        self.fields['username'].widget.attrs.update(
            {'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs', 'placeholder': 'Username'})
        self.fields['password'].widget.attrs.update(
            {'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs', 'placeholder': 'Password'})

class ProfileThemeForm(forms.ModelForm):
    """
    Form for updating Profile-specific fields like theme and profile picture.
    """
    class Meta:
        model = Profile
        fields = ['theme', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply specific styling for select and file input
        self.fields['theme'].widget.attrs.update(
            {'class': 'select select-bordered w-full bg-base-200/50 focus:outline-none focus:ring-2 focus:ring-primary/50 rounded-lg text-base-content select-xs text-xs'})
        self.fields['profile_picture'].widget.attrs.update({
            'class': 'file-input file-input-bordered w-full file-input-primary text-base-content file-input-xs text-xs'
        })


class UserDetailsForm(forms.ModelForm):
    """
    Form for updating core User model fields like first_name, last_name, email.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email'] # Only these fields for this form

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'input input-bordered w-full bg-base-200/50 focus:outline-none focus:ring-2 focus:ring-primary/50 rounded-lg text-base-content placeholder:text-base-content/40 input-xs text-xs'
            if field_name == 'email':
                field.required = True # Ensure email is required
        
        # Remove 'readonly' attributes if they were accidentally added in form init
        # The 'readonly' attribute should be controlled in the template or view context, not hardcoded in the form definition for an update form.
        # This form is meant for editing user details.
        if 'readonly' in self.fields['first_name'].widget.attrs:
            del self.fields['first_name'].widget.attrs['readonly']
        if 'readonly' in self.fields['last_name'].widget.attrs:
            del self.fields['last_name'].widget.attrs['readonly']
        if 'readonly' in self.fields['email'].widget.attrs:
            del self.fields['email'].widget.attrs['readonly']

# UserUpdateForm has been removed as UserDetailsForm serves this purpose for core user fields.
# For role updates, UserRoleAssignView handles it.
