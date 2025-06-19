# apps/payment/forms.py

from django import forms
from .models import Payment, ContributionType # Import Payment and ContributionType
from apps.individual.models import Individual
from django.forms.widgets import DateInput, NumberInput, TextInput, Select, Textarea, CheckboxInput
from django.core.exceptions import ValidationError
from django.db.models import Q # Para sa complex queries
from django.utils import timezone # Added for initial date_paid

class PaymentForm(forms.ModelForm):
    individual = forms.ModelChoiceField(
        queryset=Individual.objects.filter(
            is_active_member=True,
            is_alive=True,
            relationship='HEAD'
        ).order_by('surname', 'given_name'),
        empty_label="--- Select Payee (Head of Family) ---",
        label="Payee (Head of Family)",
        widget=Select(
            attrs={'class': 'select select-bordered w-full'}) # Removed select-sm for consistency
    )

    # Deceased Member field
    deceased_member = forms.ModelChoiceField(
        queryset=Individual.objects.filter(
            is_alive=False).order_by('surname', 'given_name'),
        empty_label="--- Select Deceased Member for Remarks ---",
        label="Remarks (Deceased Member)",
        required=False,
        widget=Select(
            attrs={'class': 'select select-bordered w-full'}) # Removed select-sm
    )

    # Field para sa legacy records
    is_legacy_record = forms.BooleanField(
        label="Old Record (No Original Receipt)",
        required=False,
        widget=CheckboxInput(attrs={'class': 'checkbox'})
    )

    class Meta:
        model = Payment
        fields = [
            'individual',
            'contribution_type',
            'amount',
            'date_paid',
            'payment_method',
            'series_prefix', # === NEW: Added series_prefix field ===
            'receipt_number',
            'deceased_member',
            'notes',
            'is_legacy_record', 
        ]
        widgets = {
            'contribution_type': Select(attrs={'class': 'select select-bordered w-full'}),
            'amount': NumberInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Enter amount'}),
            'date_paid': DateInput(attrs={'type': 'date', 'class': 'input input-bordered w-full'}),
            'payment_method': Select(attrs={'class': 'select select-bordered w-full'}),
            'series_prefix': TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'e.g., KDM-MAIN-'}), # NEW WIDGET
            'receipt_number': TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Auto-generated or N/A'}),
            'notes': Textarea(attrs={'class': 'textarea textarea-bordered w-full'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contribution_type'].queryset = ContributionType.objects.all().order_by('name')
        
        # Initial value for deceased_member
        if self.instance and self.instance.pk and self.instance.deceased_member:
            self.fields['deceased_member'].initial = self.instance.deceased_member.id

        # Para sa Legacy Record:
        # Kung nag-edit ta og existing Payment nga 'is_legacy_record', set ang initial value sa checkbox
        if self.instance and self.instance.pk:
            self.fields['is_legacy_record'].initial = self.instance.is_legacy_record
            # Disable receipt_number field kung legacy record na siya daan
            if self.instance.is_legacy_record:
                self.fields['receipt_number'].required = False
                self.fields['receipt_number'].widget.attrs['readonly'] = True
                self.fields['receipt_number'].widget.attrs['placeholder'] = 'N/A for Old Records'
            elif self.instance.receipt_number: # Kung existing payment, naay resibo, ug dili legacy, readonly na
                self.fields['receipt_number'].widget.attrs['readonly'] = True
        else: # Bag-ong payment (add mode)
            # Default behavior: receipt_number is required for new, non-legacy records
            # It should be left blank initially for auto-generation
            self.fields['receipt_number'].required = False # Allow blank for auto-generation
            self.fields['receipt_number'].widget.attrs['placeholder'] = 'Auto-generated'
            self.fields['receipt_number'].widget.attrs['readonly'] = True # Default to readonly for auto-gen
            self.fields['date_paid'].initial = timezone.localdate() # Set default date for new forms

    def clean(self):
        cleaned_data = super().clean()
        is_legacy_record = cleaned_data.get('is_legacy_record')
        receipt_number = cleaned_data.get('receipt_number')
        series_prefix = cleaned_data.get('series_prefix') # Get the new series_prefix

        # === Validation for Receipt Number when NOT legacy ===
        if not is_legacy_record:
            # If a series_prefix is provided, but no receipt_number is given, it's expected to be auto-generated.
            # If NO series_prefix and NO receipt_number, it will use the default date prefix.
            # So, only raise error if NO receipt_number AND the intention is for manual input (which isn't current flow).
            pass # The model's save method handles auto-generation if receipt_number is blank.

            # Uniqueness Validation for Receipt Number among active, non-legacy records
            if receipt_number: # Only validate if receipt number is provided (manual input or auto-generated before form clean)
                queryset = Payment.objects.filter(
                    receipt_number=receipt_number,
                    is_legacy_record=False,
                ).exclude(payment_status='CANCELLED') # Canceled receipts can have duplicate numbers
                
                if self.instance and self.instance.pk:
                    queryset = queryset.exclude(pk=self.instance.pk)

                if queryset.exists():
                    # Check the status of the existing payment for better error message
                    existing_payment = queryset.first()
                    if existing_payment.payment_status == 'PENDING_VALIDATION':
                        raise ValidationError(
                            {'receipt_number': f"This receipt number is already assigned to a payment pending validation ({existing_payment.receipt_number})."}
                        )
                    else: # VALIDATED, COMPLETED, DRAFT (active-like)
                        raise ValidationError(
                            {'receipt_number': f"This receipt number already exists for an active payment ({existing_payment.receipt_number}). Please use a unique number."}
                        )

        # === Validation for Series Prefix ===
        # If series_prefix is provided, ensure it doesn't contain invalid characters or format
        if series_prefix and not is_legacy_record:
            # Basic validation: example, prevent spaces or certain special chars if not allowed
            # You might want more specific regex validation here
            if ' ' in series_prefix or '/' in series_prefix:
                self.add_error('series_prefix', "Series prefix cannot contain spaces or '/' characters.")
            # Ensure it ends with a hyphen if it's meant for sequential numbering
            if not series_prefix.endswith('-'):
                self.add_error('series_prefix', "It is recommended that the series prefix ends with a hyphen ('-') for proper sequential numbering.")


        # If it IS a legacy record, ensure receipt_number is blank and series_prefix is also blank
        if is_legacy_record:
            # If a legacy record is marked, clear any manually entered receipt number
            if receipt_number:
                cleaned_data['receipt_number'] = None # Explicitly set to None for legacy records
            if series_prefix:
                cleaned_data['series_prefix'] = None # Clear series prefix for legacy records
                self.add_error('series_prefix', "Series prefix is not applicable for legacy records and will be ignored.")
            self.fields['receipt_number'].required = False # Make sure it's not required on submission

        return cleaned_data
