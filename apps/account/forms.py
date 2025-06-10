# apps/account/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
# from apps.common.mixins import StyledFormMixin # Assuming this mixin is defined correctly

from .models import Profile, DAISYUI_THEMES # Import Profile model at DAISYUI_THEMES

# Form para sa User Profile Settings (Theme at Profile Picture)
class ProfileThemeForm(forms.ModelForm):
    theme = forms.ChoiceField(
        choices=DAISYUI_THEMES,
        required=False,
        label="Application Theme",
        help_text="Choose your preferred color scheme for the application."
    )
    profile_picture = forms.ImageField(
        required=False,
        label="Profile Picture",
        help_text="Upload your profile picture (optional)."
    )

    class Meta:
        model = Profile
        fields = ['theme', 'profile_picture']

# Your existing StyledUserCreationForm
class StyledUserCreationForm(UserCreationForm): # Inalis ang StyledFormMixin muna para hindi mag-error kung hindi defined
    class Meta:
        model = User
        fields = ("username", "email", "first_name",
                  "last_name", "password") # Removed password1, password2 as UserCreationForm handles this

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Apply common Tailwind/DaisyUI classes to form fields
            if field_name != 'password': # Exclude password fields from general styling if needed, or customize
                field.widget.attrs.update({
                    'class': 'input input-bordered w-full' # DaisyUI input style
                })
            elif field_name in ['password', 'password2']: # For password fields, apply password-specific classes
                 field.widget.attrs.update({
                    'class': 'input input-bordered w-full'
                 })


