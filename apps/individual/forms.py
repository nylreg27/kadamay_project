# apps/individual/forms.py
from django import forms
from .models import Individual, GENDER_CHOICES, CIVIL_STATUS_CHOICES # Import Individual model at choices

class IndividualForm(forms.ModelForm):
    sex = forms.ChoiceField(
        choices=GENDER_CHOICES,
        required=True, # Mandatoryong pumili ng sex
        label="Sex"
    )
    civil_status = forms.ChoiceField(
        choices=CIVIL_STATUS_CHOICES,
        required=True, # Mandatoryong pumili ng civil status
        label="Civil Status"
    )

    class Meta:
        model = Individual
        # Isama ang lahat ng fields o ilista ang specific fields
        fields = '__all__' 
        # O kaya:
        # fields = ['surname', 'given_name', 'middle_name', 'suffix_name', 
        #           'sex', 'civil_status', 'birth_date', 'contact_number', 'email_address',
        #           'family', 'is_active_member', 'is_alive', 'relationship']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply DaisyUI/Tailwind classes to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.TextInput) or \
               isinstance(field.widget, forms.Textarea) or \
               isinstance(field.widget, forms.Select) or \
               isinstance(field.widget, forms.EmailInput) or \
               isinstance(field.widget, forms.NumberInput) or \
               isinstance(field.widget, forms.DateInput):
                field.widget.attrs.update({'class': 'input input-bordered w-full uppercase'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'checkbox checkbox-primary'})

