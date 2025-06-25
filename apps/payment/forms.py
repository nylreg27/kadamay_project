# apps/payment/forms.py (Corrected Version)

from django import forms
from django.forms import inlineformset_factory
# No need for django.db.models.Max here as it's used in the utility function/view, not directly in forms
# from django.db.models import Max

# This is the correct way to import the Payment and PaymentCoveredMember models
from .models import Payment, PaymentCoveredMember
# Import Individual and ContributionType models, as they are used directly in ModelChoiceField querysets
from apps.individual.models import Individual
from apps.contribution_type.models import ContributionType
from .utils import generate_next_or_number # Import the utility function

class PaymentForm(forms.ModelForm):
    """
    Form for the Payment model.
    """
    # These ModelChoiceFields override Django's default form fields for ForeignKeys,
    # allowing for custom querysets, labels, and empty_label.
    individual = forms.ModelChoiceField(
        queryset=Individual.objects.all().order_by('surname', 'given_name'), # Using surname, given_name for better sorting
        label="Payer",
        required=True,
        help_text="Search or select the payer.",
        empty_label="Select a Payer"
    )

    contribution_type = forms.ModelChoiceField(
        queryset=ContributionType.objects.all().order_by('name'),
        label="Contribution Type",
        required=True,
        empty_label="Select a Contribution Type"
    )

    class Meta:
        model = Payment
        fields = [
            'individual', # Now explicitly defined as ModelChoiceField
            'amount',
            'date_paid',
            'or_number',
            'payment_method',
            'gcash_reference_number',
            'contribution_type', # Now explicitly defined as ModelChoiceField
            # 'status' and 'collected_by' are handled in views/save method, not directly in form
            # 'is_validated', 'validated_by', 'remarks' are also managed by logic, not direct form fields for user input on creation
        ]
        widgets = {
            'date_paid': forms.DateInput(attrs={
                'type': 'date', # HTML5 date picker
                'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs'
            }),
            'gcash_reference_number': forms.TextInput(attrs={
                'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs',
                'placeholder': 'Enter GCash Reference Number'
            }),
            # No need to set widgets for 'individual' and 'contribution_type' here,
            # as their widgets are managed by the forms.ModelChoiceField definition.
            'payment_method': forms.Select(attrs={
                'class': 'select select-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary select-xs text-xs'
            }),
            'or_number': forms.TextInput(attrs={
                'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs',
                'placeholder': 'Auto-generated or enter manually'
            }),
            # If you want to use the Payment model's remarks field, add it here too:
            # 'remarks': forms.Textarea(attrs={'rows': 3, 'class': 'textarea textarea-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary text-xs'})
        }
        labels = {
            'individual': 'Payer',
            'amount': 'Amount',
            'date_paid': 'Date Paid',
            'or_number': 'Official Receipt No.',
            'payment_method': 'Payment Method',
            'gcash_reference_number': 'GCash Reference #',
            'contribution_type': 'Contribution Type',
            # Add label for remarks if included in fields
            # 'remarks': 'Remarks'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Apply consistent styling to fields not explicitly set in Meta.widgets
        # This will mainly affect fields not customized like 'remarks' if you add it.
        # For ModelChoiceFields (Select), the styling is applied by the select-xs class in widgets above.
        # For other types (e.g., CharField, TextField), this ensures consistency.
        for field_name, field in self.fields.items():
            if field_name not in self.Meta.widgets: # Check if a specific widget was already provided in Meta.widgets
                 # Exclude ModelChoiceFields which use <select> tags and should use select-xs not input-xs
                if not isinstance(field.widget, forms.Select):
                    current_class = field.widget.attrs.get('class', '')
                    if 'input' not in current_class: # Prevent adding input-xs if it's already a select-xs
                        field.widget.attrs['class'] = f'{current_class} input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs'.strip()
                else: # Apply select-xs for Select widgets if not already present
                    current_class = field.widget.attrs.get('class', '')
                    if 'select' not in current_class:
                        field.widget.attrs['class'] = f'{current_class} select select-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary select-xs text-xs'.strip()


        # If it's a new payment (instance is None or no pk), pre-fill OR number
        if self.instance.pk is None: # Creating a new payment
            # Check if or_number is already set (e.g., from POST data during validation)
            if 'or_number' not in self.initial or not self.initial['or_number']:
                self.initial['or_number'] = generate_next_or_number()
        # If it's an existing payment, make the or_number field readonly.
        # This prevents accidental changes to existing OR numbers.
        elif self.instance.or_number:
            self.fields['or_number'].widget.attrs['readonly'] = True


    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        gcash_reference_number = cleaned_data.get('gcash_reference_number')

        # Use 'GCASH' (uppercase) as per the choices defined in Payment model
        if payment_method == 'GCASH' and not gcash_reference_number:
            self.add_error('gcash_reference_number',
                           "GCash Reference Number is required for GCash payments.")
        return cleaned_data


# NEW: Define the CoveredMemberForm class explicitly
class CoveredMemberForm(forms.ModelForm):
    """
    Form for PaymentCoveredMember model.
    Used within the Payment formset to manage individual members covered by a payment.
    """
    # This ModelChoiceField explicitly defines the 'individual' field for the formset.
    # It ensures the correct queryset and display.
    individual = forms.ModelChoiceField(
        queryset=Individual.objects.all().order_by('surname', 'given_name'), # Order as needed
        label="Covered Member", # Custom label for this specific form
        required=True,
        empty_label="Select a Member"
    )

    class Meta:
        model = PaymentCoveredMember
        fields = ['individual', 'amount_covered'] # Exclude 'remarks' if not needed in form
        widgets = {
            # Removed the generic 'select-xs text-xs' class here as it will be applied by the individual ModelChoiceField
            # Or by crispy forms if you use {{ formset_form.individual|as_crispy_field }}
            # 'individual': forms.Select(attrs={
            #    'class': 'select select-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary select-xs text-xs'
            # }),
            'amount_covered': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs'
            })
        }
        labels = {
            'individual': 'Member Covered',
            'amount_covered': 'Amount Covered',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply styling to amount_covered if not already set by widget
        if 'amount_covered' in self.fields and 'class' not in self.fields['amount_covered'].widget.attrs:
            self.fields['amount_covered'].widget.attrs['class'] = 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs'

        # This individual field is handled by the ModelChoiceField above,
        # but if you want to apply more generic styling to it if it's a select widget
        if 'individual' in self.fields and isinstance(self.fields['individual'].widget, forms.Select):
            current_class = self.fields['individual'].widget.attrs.get('class', '')
            if 'select' not in current_class: # Ensure select-xs is applied if not already
                self.fields['individual'].widget.attrs['class'] = f'{current_class} select select-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary select-xs text-xs'.strip()


# Define the PaymentCoveredMemberFormSet using the new CoveredMemberForm class
PaymentCoveredMemberFormSet = inlineformset_factory(
    Payment,
    PaymentCoveredMember,
    form=CoveredMemberForm, # Now correctly refers to the CoveredMemberForm class
    extra=1, # Number of empty forms to display initially
    can_delete=True,
    # Widgets and labels below are redundant if defined in CoveredMemberForm directly,
    # but they can override here if needed for formset specific styling.
    # It's generally cleaner to define them directly in CoveredMemberForm.
    # Removing redundant widgets/labels here.
    # widgets={
    #     'individual': forms.Select(attrs={
    #         'class': 'select select-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary select-xs text-xs'
    #     }),
    #     'amount_covered': forms.NumberInput(attrs={
    #         'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs'
    #     })
    # },
    # labels={
    #     'individual': 'Member Covered',
    #     'amount_covered': 'Amount Covered',
    # }
)
