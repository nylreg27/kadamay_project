# apps/payment/forms.py

from django import forms
from .models import Payment, ContributionType # Import Payment and ContributionType
from apps.individual.models import Individual
from django.forms.widgets import DateInput, NumberInput, TextInput, Select, Textarea, CheckboxInput
from django.core.exceptions import ValidationError
from django.db.models import Q # Para sa complex queries

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

    # Deceased Member field (Exactly as you provided)
    deceased_member = forms.ModelChoiceField(
        queryset=Individual.objects.filter(
            is_alive=False).order_by('surname', 'given_name'),
        empty_label="--- Select Deceased Member for Remarks ---",
        label="Remarks (Deceased Member)",
        required=False,
        widget=Select(
            attrs={'class': 'select select-bordered w-full'}) # Removed select-sm
    )

    # BAG-ONG ADD: Field para sa legacy records
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
            'receipt_number',
            'deceased_member',
            'notes',
            'is_legacy_record', # DUGANGI NI SA FIELDS
        ]
        widgets = {
            'contribution_type': Select(attrs={'class': 'select select-bordered w-full'}), # Removed select-sm
            'amount': NumberInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Enter amount'}), # Removed input-sm
            'date_paid': DateInput(attrs={'type': 'date', 'class': 'input input-bordered w-full'}), # Removed input-sm
            'payment_method': Select(attrs={'class': 'select select-bordered w-full'}), # Removed select-sm
            # Ang receipt_number dili na required sa forms.py, atong i-handle ang validation sa clean method
            'receipt_number': TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Auto-generated or N/A'}), # Removed input-sm
            'notes': Textarea(attrs={'class': 'textarea textarea-bordered w-full'}), # Removed textarea-sm
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contribution_type'].queryset = ContributionType.objects.all().order_by('name')
        
        # Initial value for deceased_member (as per your existing code)
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
            self.fields['receipt_number'].required = True # Set initial requirement
            # It should be left blank initially for auto-generation
            self.fields['receipt_number'].widget.attrs['placeholder'] = 'Auto-generated'
            self.fields['receipt_number'].widget.attrs['readonly'] = True # Default to readonly for auto-gen


    def clean(self):
        cleaned_data = super().clean()
        is_legacy_record = cleaned_data.get('is_legacy_record')
        receipt_number = cleaned_data.get('receipt_number')
        
        # === Uniqueness Validation for Receipt Number ===
        # ONLY validate uniqueness for non-legacy records AND if receipt_number is provided
        if not is_legacy_record and receipt_number:
            # Check if an active/non-cancelled/non-legacy payment with this receipt_number already exists
            # Exclude the current instance if we are updating an existing payment
            queryset = Payment.objects.filter(
                receipt_number=receipt_number,
                is_legacy_record=False,
            ).exclude(payment_status='CANCELLED') # Canceled receipts can have duplicate numbers
            
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk) # Exclude current object during update

            if queryset.exists():
                raise ValidationError(
                    {'receipt_number': 'This receipt number already exists for an active payment. Please use a unique number.'}
                )
        
        # === Receipt Number Requirement based on Legacy Status ===
        # If it's NOT a legacy record, and no receipt_number is provided
        if not is_legacy_record and not receipt_number:
            # This should ideally be handled by auto-generation in model's save method,
            # but this validation ensures the form understands it's needed for non-legacy.
            # We'll allow blank here as the model's save will fill it.
            # If you want to force manual input for some reason before save:
            # raise ValidationError({'receipt_number': 'Receipt Number is required for new, non-legacy payments.'})
            pass # Allow blank if auto-generation is expected

        # If it IS a legacy record, ensure receipt_number is blank or a specific format for legacy
        if is_legacy_record and receipt_number:
            # If a legacy record is marked, but a receipt_number is entered, consider this a warning
            # Or you can force it to be blank
            # For now, we will allow it but the save method will handle setting to None if needed
            pass

        return cleaned_data

