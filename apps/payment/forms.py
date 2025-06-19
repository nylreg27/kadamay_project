# apps/payment/forms.py
from django import forms
from django.forms import inlineformset_factory
# Ensure all necessary models and choices are imported
from .models import Payment, CoveredMember, Individual, Church, ContributionType, PAYMENT_METHOD_CHOICES 

class PaymentForm(forms.ModelForm):
    # Override fields to use custom widgets or attributes
    date_paid = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered w-full'}),
        label="Date of Payment"
    )
    amount = forms.DecimalField(
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'input input-bordered w-full'}),
        label="Total Amount Paid"
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'}),
        label="Payment Method"
    )
    gcash_reference_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'GCash Reference Number'}),
        label="GCash Ref. No.",
        help_text="Required if payment method is GCash."
    )
    church = forms.ModelChoiceField(
        queryset=Church.objects.all(),
        required=False, 
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'}),
        label="Church (Optional)"
    )
    contribution_type = forms.ModelChoiceField(
        queryset=ContributionType.objects.all(),
        required=False, 
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'}),
        label="Contribution Type (Optional)"
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'textarea textarea-bordered h-24 w-full', 'placeholder': 'Any additional notes...'}),
        required=False,
        label="Notes"
    )
    
    # receipt_number should be read-only if auto-generated, or just HiddenInput
    # If you want it visible but not editable, use forms.TextInput and disabled=True in attrs
    receipt_number = forms.CharField(widget=forms.HiddenInput(), required=False) 
    
    # These fields are typically set by the view or model's save method using the request.user
    # So we often don't need them as form fields, or they should be HiddenInput.
    # If they are ModelChoiceFields, they need a queryset.
    # If your model's save method sets these, you might remove them from the form fields list entirely
    # and rely on the model's logic. But if they're here for some reason, they need querysets.
    # For now, let's keep them as HiddenInput and let the view/model handle setting the user instance.
    collected_by = forms.ModelChoiceField(queryset=Individual.objects.all(), widget=forms.HiddenInput(), required=False)
    created_by = forms.ModelChoiceField(queryset=Individual.objects.all(), widget=forms.HiddenInput(), required=False)
    updated_by = forms.ModelChoiceField(queryset=Individual.objects.all(), widget=forms.HiddenInput(), required=False)


    class Meta:
        model = Payment
        fields = [
            'receipt_number', 'date_paid', 'amount', 'payment_method', 'gcash_reference_number',
            'church', 'contribution_type', 'notes', 
            # Include collected_by, created_by, updated_by if they are truly part of the form submission
            # even if hidden. If they are set in the model's save method or view directly,
            # you can remove them from fields here.
            'collected_by', 'created_by', 'updated_by' 
        ]
        exclude = [
            'payment_status', 'validated_by', 'validation_date', 'is_cancelled', 
            'cancellation_date', 'cancellation_reason', 'cancelled_by',
            'individual', 'deceased_member' # Exclude these as CoveredMember handles allocations
        ]
    
    def __init__(self, *args, **kwargs):
        # Pop 'user' from kwargs if passed, used for setting initial/queryset for user-related fields
        self.user = kwargs.pop('user', None) # <--- ADD THIS LINE to handle 'user' from view
        super().__init__(*args, **kwargs)

        # Populate queryset for collected_by, created_by, updated_by if they are meant to be users
        # For simplicity, if these are really auto-set by the model's save(), you might exclude them from 'fields'
        # in Meta and remove these lines.
        # If they are meant to refer to a specific Individual from the database, then keep this.
        # Assuming they should be set to the User, and not an Individual:
        # If your Payment model's `collected_by`, `created_by`, `updated_by` are ForeignKey to Django's User model:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if self.fields.get('collected_by'):
            self.fields['collected_by'].queryset = User.objects.all()
        if self.fields.get('created_by'):
            self.fields['created_by'].queryset = User.objects.all()
        if self.fields.get('updated_by'):
            self.fields['updated_by'].queryset = User.objects.all()
        
        # Add basic styling to all fields (skip hidden fields for visual class)
        for field_name, field in self.fields.items():
            if field_name not in ['receipt_number', 'collected_by', 'created_by', 'updated_by']: # Skip hidden fields
                if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.Textarea, forms.DateInput)):
                    if 'class' not in field.widget.attrs or not field.widget.attrs['class']:
                        field.widget.attrs.update({'class': 'input input-bordered w-full'})
                elif isinstance(field.widget, forms.Select):
                    if 'class' not in field.widget.attrs or not field.widget.attrs['class']:
                        field.widget.attrs.update({'class': 'select select-bordered w-full'})

        # Dynamically set initial value for payment_method or church if needed
        # self.fields['payment_method'].initial = 'CASH'
        # self.fields['church'].initial = Church.objects.first() # Example: default to first church


class CoveredMemberForm(forms.ModelForm):
    individual = forms.ModelChoiceField(
        queryset=Individual.objects.all().select_related('family'), # Optimize query
        # Add 'select2-individual' class here for consistency with JS
        widget=forms.Select(attrs={'class': 'select select-bordered w-full payee-select select2-individual'}), # <--- ADDED select2-individual here
        label="Payee"
    )
    amount_allocated = forms.DecimalField(
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'input input-bordered w-full amount-allocated'}),
        label="Amount Allocated"
    )
    notes = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Notes for this payee...'}),
        required=False,
        label="Notes"
    )

    class Meta:
        model = CoveredMember
        fields = ['individual', 'amount_allocated', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['individual'].empty_label = "Select an individual"
        
        # Add a custom data attribute for easier JS manipulation
        # Make sure individual.id is available if instance exists
        if self.instance and self.instance.individual:
            self.fields['individual'].widget.attrs['data-individual-id'] = self.instance.individual.id
        else:
            self.fields['individual'].widget.attrs['data-individual-id'] = '' # Ensure it's always set

# Create a formset for CoveredMember. This allows multiple CoveredMember forms within one Payment form.
PayeeFormSet = inlineformset_factory(
    Payment, # Parent model
    CoveredMember, # Child model
    form=CoveredMemberForm,
    extra=1, # Start with one empty form
    can_delete=True, # Allow deleting existing forms
    min_num=1, # At least one payee
    validate_min=True # Enforce min_num validation
)
