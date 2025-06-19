# apps/individual/forms.py

from django import forms
from .models import Individual  # Import Individual model
# Import Family model if needed for form choices
from apps.family.models import Family
# Import Church model if needed for form choices
from apps.church.models import Church


class IndividualForm(forms.ModelForm):
    class Meta:
        model = Individual
        # FIXED: EXCLUDE 'membership_id' and 'date_added' from the form fields.
        # Kay automatic na sila ma-generate sa save method sa model.
        # Apil lang ang tanan nga fields nga gusto nimong ipakita ug i-edit.
        exclude = ['membership_id', 'date_added']
        # Alternative: use 'fields' if you want to explicitly list all other fields
        # fields = [
        #     'given_name', 'middle_name', 'surname', 'suffix_name',
        #     'sex', 'civil_status', 'birth_date', 'contact_number',
        #     'email_address', 'address', 'relationship',
        #     'membership_status', 'is_active_member', 'is_alive',
        #     'family', 'church'
        # ]

        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered w-full'}),
            # Add or adjust widgets for other fields as per your design
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Apply DaisyUI/Tailwind classes to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (
                forms.TextInput,
                forms.EmailInput,
                forms.NumberInput,
                forms.DateInput,
            )):
                field.widget.attrs.update(
                    {'class': 'input input-bordered w-full uppercase'})
            elif isinstance(field.widget, (forms.Select)):
                field.widget.attrs.update(
                    {'class': 'select select-bordered w-full uppercase'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update(
                    {'class': 'textarea textarea-bordered w-full h-20 uppercase'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update(
                    {'class': 'checkbox checkbox-primary'})

        # You can further customize specific fields if needed
        # Example for family and church dropdowns:
        if 'family' in self.fields:
            self.fields['family'].queryset = Family.objects.all().order_by(
                'family_name')
            self.fields['family'].empty_label = "-- Select Family --"

        if 'church' in self.fields:
            self.fields['church'].queryset = Church.objects.all().order_by(
                'name')
            self.fields['church'].empty_label = "-- Select Church --"
