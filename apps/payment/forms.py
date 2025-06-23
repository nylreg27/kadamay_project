# apps/payment/forms.py

from django import forms
from django.forms import inlineformset_factory
# This is the correct way to import the Payment model from models.py
from .models import Payment, PaymentCoveredMember
from apps.individual.models import Individual
from apps.contribution_type.models import ContributionType


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
        model = Payment # This line correctly refers to the Payment model imported from .models
        fields = [
            'individual',
            'amount',
            'date_paid',
            'payment_method',
            'gcash_reference_number',
            'contribution_type',
        ]
        widgets = {
            'date_paid': forms.DateInput(attrs={'type': 'date', 'class': 'form-input rounded-md shadow-sm mt-1 block w-full'}),
            'amount': forms.NumberInput(attrs={'class': 'form-input rounded-md shadow-sm mt-1 block w-full'}),
            'gcash_reference_number': forms.TextInput(attrs={'class': 'form-input rounded-md shadow-sm mt-1 block w-full', 'placeholder': 'Enter GCash Reference Number'}),
            'individual': forms.Select(attrs={'class': 'form-select rounded-md shadow-sm mt-1 block w-full'}),
            'contribution_type': forms.Select(attrs={'class': 'form-select rounded-md shadow-sm mt-1 block w-full'}),
            'payment_method': forms.Select(attrs={'class': 'form-select rounded-md shadow-sm mt-1 block w-full'}),
        }
        labels = {
            'individual': 'Payer',
            'amount': 'Amount',
            'date_paid': 'Date Paid',
            'payment_method': 'Payment Method',
            'gcash_reference_number': 'GCash Reference #',
            'contribution_type': 'Contribution Type',
        }

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        gcash_reference_number = cleaned_data.get('gcash_reference_number')

        if payment_method == 'gcash' and not gcash_reference_number:
            self.add_error('gcash_reference_number',
                           "GCash Reference Number is required for GCash payments.")
        return cleaned_data


PaymentCoveredMemberFormSet = inlineformset_factory(
    Payment,
    PaymentCoveredMember,
    fields=['individual', 'amount_covered'],
    extra=1,
    can_delete=True,
    widgets={
        'individual': forms.Select(attrs={'class': 'form-select rounded-md shadow-sm mt-1 block w-full'}),
        'amount_covered': forms.NumberInput(attrs={'class': 'form-input rounded-md shadow-sm mt-1 block w-full'})
    },
    labels={
        'individual': 'Member Covered',
        'amount_covered': 'Amount Covered',
    }
)