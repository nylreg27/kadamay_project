from django import forms
from .models import Individual
from apps.family.models import Family
from apps.payment.models import Payment


class IndividualForm(forms.ModelForm):
    class Meta:
        model = Individual
        fields = '__all__'
        widgets = {
            'membership_status': forms.HiddenInput(),  # Hides field from UI
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If creating a new instance, set default membership_status to 'ACTIVE'
        if not self.instance.pk:
            self.fields['membership_status'].initial = 'ACTIVE'

        # Apply consistent Tailwind CSS classes
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (
                forms.TextInput,
                forms.EmailInput,
                forms.Textarea,
                forms.Select,
                forms.NumberInput,
                forms.DateInput,
                forms.URLInput,
                forms.PasswordInput,
            )):
                current_classes = field.widget.attrs.get('class', '')
                new_classes = 'input input-bordered w-full'
                field.widget.attrs.update(
                    {'class': f"{current_classes} {new_classes}".strip()})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update(
                    {'class': 'checkbox checkbox-primary'})
            elif isinstance(field.widget, forms.RadioSelect):
                field.widget.attrs.update(
                    {'class': 'radio radio-primary'})

        # Family field: hide if pre-populated via initial data
        if 'family' in self.initial and self.initial['family']:
            self.fields['family'].widget = forms.HiddenInput()
            self.fields['family'].required = False
        else:
            self.fields['family'].queryset = Family.objects.all().order_by(
                'family_name')
            self.fields['family'].empty_label = "Select Family"


class PaymentForm(forms.ModelForm):
    # If you want the individual field to be hidden and pre-filled by the URL
    # individual = forms.ModelChoiceField(queryset=Individual.objects.all(), widget=forms.HiddenInput())

    class Meta:
        model = Payment
        # Or specify your fields: ['individual', 'date', 'description', 'amount', 'receipt_no']
        fields = '__all__'
        widgets = {
            # HTML5 date input
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
