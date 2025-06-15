# apps/account/forms.py
from django import forms
# Added AuthenticationForm for UserLoginForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
# No need to import THEME_CHOICES directly, it's part of Profile
from .models import Profile

User = get_user_model()


class ProfileThemeForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['theme', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply DaisyUI classes
        self.fields['theme'].widget.attrs.update(
            {'class': 'select select-bordered w-full max-w-xs'})

        self.fields.get('profile_picture', forms.CharField()).widget.attrs.update(
            {'class': 'file-input file-input-bordered w-full max-w-xs'})


class StyledUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        # UserCreationForm already handles password fields.
        fields = ("username", "email", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'input input-bordered w-full'  # DaisyUI input style
            })

# Assuming this is your custom login form


# <--- This class must exist and be named correctly
class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {'class': 'input input-bordered w-full'})
        self.fields['password'].widget.attrs.update(
            {'class': 'input input-bordered w-full'})
