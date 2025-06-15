# apps/family/forms.py
from django import forms
from .models import Family
from apps.church.models import Church # Import Church model para sa queryset

class FamilyForm(forms.ModelForm):
    class Meta:
        model = Family
        # Siguraduhin na kasama ang 'church' field
        fields = ['family_name', 'address', 'church', 'is_active'] 
        # Maaaring idagdag ang 'head_member' at 'contact_number' kung kasama sila sa iyong Family model
        # fields = ['family_name', 'address', 'church', 'is_active', 'head_member', 'contact_number']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # I-apply ang DaisyUI/Tailwind classes sa lahat ng fields
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

        # Custom handling para sa 'church' field
        # Kung may initial value na ang 'church' (ibig sabihin, galing sa FamilyCreateInChurchView)
        if 'church' in self.initial and self.initial['church']:
            self.fields['church'].widget = forms.HiddenInput() # Itago ang field
            self.fields['church'].required = False # Hindi na required kung pre-populated
        else:
            # Kung walang initial church, ipakita ang dropdown
            self.fields['church'].queryset = Church.objects.all().order_by('name') # I-load lahat ng churches
            self.fields['church'].empty_label = "Select Church" # Placeholder option

