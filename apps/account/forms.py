# E:\my_project\kadamay_project\apps\account\forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()


class StyledUserCreationForm(UserCreationForm):
    # Role field, using choices defined in Profile model
    role = forms.ChoiceField(
        choices=Profile.USER_ROLES,
        label='ROLE',
        # DaisyUI and Tailwind classes for styling
        widget=forms.Select(attrs={
                            'class': 'select select-bordered w-full uppercase focus:outline-none focus:ring-2 focus:ring-primary select-xs text-xs'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + \
            ('email', 'first_name', 'last_name',)  # Add custom fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Loop through all fields to apply consistent styling
        for field_name, field in self.fields.items():
            if field_name not in ['role', 'password', 'password2', 'is_active', 'is_staff', 'is_superuser']:
                # Apply input styling for text-based fields
                field.widget.attrs.update({
                    # Small input size, 12px text
                    'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs'
                })
            elif field_name in ['is_active', 'is_staff', 'is_superuser']:
                # Apply checkbox styling
                field.widget.attrs.update(
                    {'class': 'checkbox checkbox-primary'})

        # Set placeholders for relevant fields
        if 'username' in self.fields:
            self.fields['username'].widget.attrs['placeholder'] = 'Choose a username'
        if 'email' in self.fields:
            self.fields['email'].widget.attrs['placeholder'] = 'Enter email address'
        if 'first_name' in self.fields:
            self.fields['first_name'].widget.attrs['placeholder'] = 'Enter first name'
        if 'last_name' in self.fields:
            self.fields['last_name'].widget.attrs['placeholder'] = 'Enter last name'

        # Ensure password fields also have small text. Password fields typically don't take a placeholder due to security.
        if 'password' in self.fields:
            self.fields['password'].widget.attrs.update({
                'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs'
            })
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({
                'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs'
            })

    def save(self, commit=True):
        # Save the User instance
        user = super().save(commit=commit)
        if commit:
            # Create or get the Profile for the new user and set the role
            profile, created = Profile.objects.get_or_create(user=user)
            profile.role = self.cleaned_data['role']
            profile.save()
        return user


class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply styling to username and password fields for login form
        self.fields['username'].widget.attrs.update(
            {'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs', 'placeholder': 'Username'})
        self.fields['password'].widget.attrs.update(
            {'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs', 'placeholder': 'Password'})


class ProfileThemeForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['theme', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['theme'].widget.attrs.update(
            {'class': 'select select-bordered w-full bg-base-200/50 focus:outline-none focus:ring-2 focus:ring-primary/50 rounded-lg text-base-content select-xs text-xs'})
        self.fields['profile_picture'].widget.attrs.update({
            'class': 'file-input file-input-bordered w-full file-input-primary text-base-content file-input-xs text-xs'
        })


class UserDetailsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'input input-bordered w-full bg-base-200/50 focus:outline-none focus:ring-2 focus:ring-primary/50 rounded-lg text-base-content placeholder:text-base-content/40 input-xs text-xs'
            if field_name == 'email':
                field.required = True


class UserUpdateForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=Profile.USER_ROLES,
        label='ROLE',
        widget=forms.Select(attrs={
                            'class': 'select select-bordered w-full uppercase focus:outline-none focus:ring-2 focus:ring-primary select-xs text-xs'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name',
                  'last_name', 'is_active', 'is_staff', 'is_superuser']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['role'].initial = self.instance.profile.role

        for field_name, field in self.fields.items():
            if field_name not in ['role', 'is_active', 'is_staff', 'is_superuser']:
                field.widget.attrs.update(
                    {'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs'})
            elif field_name in ['is_active', 'is_staff', 'is_superuser']:
                field.widget.attrs.update(
                    {'class': 'checkbox checkbox-primary'})

        self.fields['username'].widget.attrs['readonly'] = 'readonly'
        self.fields['username'].widget.attrs['class'] += ' input-disabled'
        self.fields['username'].help_text = 'Username cannot be changed.'
