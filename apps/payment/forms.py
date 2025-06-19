# apps/payment/forms.py

from django import forms
from django.forms import inlineformset_factory # Import inlineformset_factory
from .models import Payment, ContributionType, PaymentIndividualAllocation
from apps.individual.models import Individual
from django.forms.widgets import DateInput, NumberInput, TextInput, Select, Textarea, CheckboxInput
from django.core.exceptions import ValidationError
from django.db.models import Q # Para sa complex queries
from django.utils import timezone # Added for initial date_paid
import datetime

class PaymentForm(forms.ModelForm):
    # Payee selection: Only active, alive heads of family
    individual = forms.ModelChoiceField(
        queryset=Individual.objects.filter(
            is_active_member=True,
            is_alive=True,
            relationship='HEAD'
        ).order_by('surname', 'given_name'),
        empty_label="--- Select Payee (Head of Family) ---",
        label="Payee (Head of Family)",
        widget=Select(
            attrs={'class': 'select select-bordered w-full'})
    )

    # Deceased Member field (optional, for remarks related to a deceased person)
    deceased_member = forms.ModelChoiceField(
        queryset=Individual.objects.filter(
            is_alive=False).order_by('surname', 'given_name'),
        empty_label="--- Select Deceased Member for Remarks ---",
        label="Remarks (Deceased Member)",
        required=False,
        widget=Select(
            attrs={'class': 'select select-bordered w-full'})
    )

    # Field para sa legacy records
    is_legacy_record = forms.BooleanField(
        label="Is this a Legacy Record (Manual OR Number)?",
        required=False,
        widget=CheckboxInput(attrs={'class': 'checkbox checkbox-primary'})
    )
    
    # Series Prefix for auto-generated ORs
    series_prefix = forms.CharField(
        max_length=10,
        required=False,
        label="Receipt Series Prefix (e.g., OR-)",
        help_text="Optional prefix for auto-generated OR numbers. Defaults to 'OR-'."
    )

    class Meta:
        model = Payment
        fields = [
            'individual', 'church', 'contribution_type', 'date_paid',
            'amount', 'payment_method', 'notes', 'deceased_member',
            'is_legacy_record', 'receipt_number', 'series_prefix'
        ]
        widgets = {
            'date_paid': DateInput(attrs={'type': 'date', 'class': 'input input-bordered w-full'}),
            'amount': NumberInput(attrs={'class': 'input input-bordered w-full', 'step': '0.01'}),
            'church': Select(attrs={'class': 'select select-bordered w-full'}),
            'contribution_type': Select(attrs={'class': 'select select-bordered w-full'}),
            'payment_method': Select(attrs={'class': 'select select-bordered w-full'}),
            'notes': Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
            'receipt_number': TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Auto-generated or enter manually for legacy'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial date_paid to today if new instance
        if not self.instance.pk:
            self.fields['date_paid'].initial = timezone.now().date()
            # Set default payment_status for new payments
            self.instance.payment_status = 'DRAFT'
        
        # Adjust 'receipt_number' and 'series_prefix' required status based on 'is_legacy_record'
        # This is for initial load; clean method will handle final validation
        if self.instance.pk and self.instance.is_legacy_record:
            self.fields['receipt_number'].required = True
            self.fields['series_prefix'].widget = forms.HiddenInput()
            self.fields['series_prefix'].required = False
            self.fields['receipt_number'].widget.attrs['readonly'] = True # Legacy ORs are read-only
        elif self.instance.pk and not self.instance.is_legacy_record:
            self.fields['receipt_number'].widget.attrs['readonly'] = True # Auto-generated ORs are read-only
            self.fields['receipt_number'].required = False
        else: # New record
            # Initially, make receipt_number not required (it will be auto-generated)
            self.fields['receipt_number'].required = False
            # Make series_prefix not required
            self.fields['series_prefix'].required = False
        
        # Apply consistent styling to all fields not already handled by widgets
        for field_name, field in self.fields.items():
            if field_name not in self.Meta.widgets and isinstance(field.widget, (TextInput, Select, NumberInput, DateInput, Textarea)):
                current_classes = field.widget.attrs.get('class', '')
                new_classes = 'input input-bordered w-full'
                if isinstance(field.widget, Textarea):
                     new_classes = 'textarea textarea-bordered w-full'
                elif isinstance(field.widget, Select):
                     new_classes = 'select select-bordered w-full'
                field.widget.attrs.update({'class': f"{current_classes} {new_classes}".strip()})


    def clean(self):
        cleaned_data = super().clean()
        is_legacy_record = cleaned_data.get('is_legacy_record')
        receipt_number = cleaned_data.get('receipt_number')
        series_prefix = cleaned_data.get('series_prefix')
        
        # If it's a legacy record, receipt_number is required and series_prefix should be empty
        if is_legacy_record:
            if not receipt_number:
                self.add_error('receipt_number', "Receipt number is required for legacy records.")
            # Ensure series_prefix is not set for legacy records
            if series_prefix:
                cleaned_data['series_prefix'] = None
                self.add_error('series_prefix', "Series prefix is not applicable for legacy records and will be ignored.")
        else: # Not a legacy record, receipt_number will be auto-generated
            # Receipt number should be empty for auto-generated
            if receipt_number:
                self.add_error('receipt_number', "Receipt number will be auto-generated. Do not enter it for non-legacy records.")
            # If series_prefix is provided, ensure it doesn't contain invalid characters or format
            if series_prefix:
                # Basic validation: example, prevent spaces or certain special chars if not allowed
                if ' ' in series_prefix or '/' in series_prefix or '\\' in series_prefix:
                    self.add_error('series_prefix', "Series prefix cannot contain spaces, '/', or '\\' characters.")
                # Ensure it ends with a hyphen if it's meant for sequential numbering
                if not series_prefix.endswith('-') and len(series_prefix) > 0: # Allow empty string or non-hyphen if it's just a label
                    # Optional: enforce hyphen for sequence, or allow flexible prefix.
                    # For now, a soft recommendation.
                    pass # self.add_error('series_prefix', "It is recommended that the series prefix ends with a hyphen ('-') for proper sequential numbering.")
            
            # For new, non-legacy records, ensure receipt_number is None for auto-generation
            if not self.instance.pk: # Only for new instances
                cleaned_data['receipt_number'] = None

        # Custom validation for amount vs. allocations will be in the view's form_valid
        return cleaned_data


class PaymentIndividualAllocationForm(forms.ModelForm):
    # Override individual field to filter for active, alive members (not necessarily HEAD)
    # and to use a nicer widget
    individual = forms.ModelChoiceField(
        queryset=Individual.objects.filter(is_active_member=True, is_alive=True).order_by('surname', 'given_name'),
        label="Covered Member",
        widget=Select(attrs={'class': 'select select-bordered w-full select-sm'})
    )
    
    class Meta:
        model = PaymentIndividualAllocation
        fields = ['individual', 'allocated_amount']
        widgets = {
            'allocated_amount': NumberInput(attrs={'class': 'input input-bordered w-full input-sm', 'step': '0.01'}),
            # 'notes': TextInput(attrs={'class': 'input input-bordered w-full input-sm', 'placeholder': 'Optional remarks for this allocation'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply consistent styling to all fields
        for field_name, field in self.fields.items():
            current_classes = field.widget.attrs.get('class', '')
            if field_name == 'individual':
                field.widget.attrs.update({'class': f"{current_classes} select select-bordered w-full select-sm".strip()})
            elif field_name == 'allocated_amount':
                field.widget.attrs.update({'class': f"{current_classes} input input-bordered w-full input-sm".strip()})
            elif field_name == 'remarks':
                field.widget.attrs.update({'class': f"{current_classes} input input-bordered w-full input-sm".strip()})


# Create an inline formset for PaymentIndividualAllocation
PaymentIndividualAllocationFormSet = inlineformset_factory(
    Payment,                      # Parent model
    PaymentIndividualAllocation,  # Child model
    form=PaymentIndividualAllocationForm,
    extra=1,                      # Number of empty forms to display
    can_delete=True,              # Allow deleting existing allocations
    min_num=1,                    # Require at least one allocation
    validate_min=True,
)