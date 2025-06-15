# apps/church/forms.py (Full and Corrected Version)

from django import forms
from .models import Church, District
# Import get_user_model for in_charge field
from django.contrib.auth import get_user_model

User = get_user_model()  # Get the active user model


class ChurchForm(forms.ModelForm):
    class Meta:
        model = Church
        fields = ['name', 'address', 'district', 'is_active', 'in_charge']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['district'].queryset = District.objects.all().order_by(
            'name')  # Order districts
        self.fields['district'].label_from_instance = lambda obj: obj.name

        # Ensure that 'in_charge' uses Django's built-in User model
        self.fields['in_charge'].queryset = User.objects.all().order_by(
            'last_name', 'first_name')
        # Display full name of the user, or username if names are empty
        self.fields['in_charge'].label_from_instance = lambda obj: f"{obj.first_name} {obj.last_name}" if obj.first_name or obj.last_name else obj.username
