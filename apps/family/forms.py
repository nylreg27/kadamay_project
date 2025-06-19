# apps/family/forms.py
from django import forms
from .models import Family
from apps.church.models import Church
# <-- Import Individual para sa 'head_of_family' queryset
from apps.individual.models import Individual


class FamilyForm(forms.ModelForm):
    class Meta:
        model = Family
        # FIXED AGAIN: Karon, 'head_of_family' na gyud ang field ug apil na ang 'contact_number'
        # Gitangtang ang 'in_charge' ug gibutang ang 'head_of_family'
        fields = ['family_name', 'address', 'church',
                  'head_of_family', 'contact_number', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # I-apply ang DaisyUI/Tailwind classes sa tanan nga fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (
                forms.TextInput,
                forms.Textarea,
                forms.EmailInput,
                forms.NumberInput,
                forms.DateInput
            )):
                # Default class para sa text-based inputs ug date inputs
                field.widget.attrs.update(
                    {'class': 'input input-bordered w-full uppercase'})
            elif isinstance(field.widget, forms.Select):
                # Default class para sa select/dropdowns
                field.widget.attrs.update(
                    {'class': 'select select-bordered w-full uppercase'})
            elif isinstance(field.widget, forms.CheckboxInput):
                # Default class para sa checkboxes
                field.widget.attrs.update(
                    {'class': 'checkbox checkbox-primary'})

        # Specific handling ug queryset para sa 'head_of_family' field
        # Siguraduhon nga ang 'head_of_family' field na-initialize og sakto sa queryset
        if 'head_of_family' in self.fields:
            self.fields['head_of_family'].queryset = Individual.objects.all().order_by(
                'surname', 'given_name')
            self.fields['head_of_family'].empty_label = "-- Pilia ang Ulo sa Pamilya --"

        # Custom handling para sa 'church' field
        if 'church' in self.initial and self.initial['church']:
            self.fields['church'].widget = forms.HiddenInput()
            self.fields['church'].required = False
        else:
            self.fields['church'].queryset = Church.objects.all().order_by(
                'name')
            self.fields['church'].empty_label = "Pilia ang Simbahan"
