# apps/account/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Profile # Import Profile model

User = get_user_model()

# Custom form for user registration
class StyledUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'input input-bordered w-full'  # DaisyUI input style
            })

# Custom form for user login
class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {'class': 'input input-bordered w-full'})
        self.fields['password'].widget.attrs.update(
            {'class': 'input input-bordered w-full'})

# Form for Profile settings (theme and profile picture)
class ProfileThemeForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['theme', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply DaisyUI classes
        self.fields['theme'].widget.attrs.update(
            {'class': 'select select-bordered w-full bg-base-200/50 focus:outline-none focus:ring-2 focus:ring-primary/50 rounded-lg text-sm text-base-content select-sm'}) # Added bg and focus styles

# Form para sa personal details sa User (First Name, Last Name, Email)
class UserDetailsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply DaisyUI/Tailwind classes directly to fields for consistency
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'input input-bordered w-full bg-base-200/50 focus:outline-none focus:ring-2 focus:ring-primary/50 rounded-lg text-sm text-base-content placeholder:text-base-content/40 input-sm'
            # Make email required if it's not already by default
            if field_name == 'email':
                field.required = True