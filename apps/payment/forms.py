# apps/payment/forms.py

from django import forms
from django.forms import inlineformset_factory
from django.db.models import Max
# This is the correct way to import the Payment model from models.py
from .models import Payment, PaymentCoveredMember
from apps.individual.models import Individual
from apps.contribution_type.models import ContributionType
from .utils import generate_next_or_number  # Import the new utility function


class PaymentForm(forms.ModelForm):
    """
    Form for the Payment model.
    """
    individual = forms.ModelChoiceField(
        queryset=Individual.objects.all().order_by('given_name', 'surname'),
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
            'individual',
            'amount',
            'date_paid',
            'or_number',  # ATING IDUGANG ANG OR_NUMBER FIELD SA FORM PARA SA MANUAL INPUT IF NEEDED
            'payment_method',
            'gcash_reference_number',
            'contribution_type',
            # status and collected_by are handled in views/save method.
            # audited fields (validated_by, cancelled_by, etc.) are also handled in views.
        ]
        widgets = {
            'date_paid': forms.DateInput(attrs={
                'type': 'date',
                'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs'
            }),
            'gcash_reference_number': forms.TextInput(attrs={
                'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs',
                'placeholder': 'Enter GCash Reference Number'
            }),
            'individual': forms.Select(attrs={
                'class': 'select select-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary select-xs text-xs'
            }),
            'contribution_type': forms.Select(attrs={
                'class': 'select select-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary select-xs text-xs'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'select select-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary select-xs text-xs'
            }),
            'or_number': forms.TextInput(attrs={  # Styling for OR number
                'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs',
                'placeholder': 'Auto-generated or enter manually'
            }),
        }
        labels = {
            'individual': 'Payer',
            'amount': 'Amount',
            'date_paid': 'Date Paid',
            'or_number': 'Official Receipt No.',  # Label for OR number
            'payment_method': 'Payment Method',
            'gcash_reference_number': 'GCash Reference #',
            'contribution_type': 'Contribution Type',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply consistent styling to all fields if not already done by widgets
        for field_name, field in self.fields.items():
            if field_name not in self.Meta.widgets:  # Only apply if no specific widget class was set
                field.widget.attrs.update({
                    'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs'
                })

        # If it's a new payment (instance is None), pre-fill OR number
        # or_number is now in fields, so we need to set its initial value.
        if self.instance.pk is None:  # Creating a new payment
            # Check if or_number is already set (e.g., from POST data)
            # If not, generate it
            if 'or_number' not in self.initial or not self.initial['or_number']:
                self.initial['or_number'] = generate_next_or_number()
            # Make or_number field read-only if it's auto-generated,
            # but allow manual input if they clear it.
            # For simplicity for now, let's just pre-fill.
            # Later, we can add JS to make it readonly unless edited.

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        gcash_reference_number = cleaned_data.get('gcash_reference_number')

        if payment_method == 'gcash' and not gcash_reference_number:
            self.add_error('gcash_reference_number',
                           "GCash Reference Number is required for GCash payments.")
        return cleaned_data

    # We will let the view handle the save process for the main Payment object
    # to ensure OR number is handled correctly before saving, and then save formsets.


# Formset for PaymentCoveredMember (multiple payees)
PaymentCoveredMemberFormSet = inlineformset_factory(
    Payment,
    PaymentCoveredMember,
    fields=['individual', 'amount_covered'],
    extra=1,  # Number of empty forms to display
    can_delete=True,
    widgets={
        'individual': forms.Select(attrs={
            'class': 'select select-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary select-xs text-xs'
        }),
        'amount_covered': forms.NumberInput(attrs={
            'class': 'input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary input-xs text-xs'
        })
    },
    labels={
        'individual': 'Member Covered',
        'amount_covered': 'Amount Covered',
    }
)
