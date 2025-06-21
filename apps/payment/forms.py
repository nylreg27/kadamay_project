# apps/payment/forms.py

from django import forms
# Para sa CoveredMember multiple entries
from django.forms import inlineformset_factory
from .models import Payment, CoveredMember
# Import sa Individual ug ContributionType para sa mga choices sa form
# HINUMDOMI: Kung kini nga imports ang hinungdan sa circular import,
# kinahanglan nimo i-import ni sila INSIDE sa init method sa form,
# pero sa karon, try lang nato direkta.
from apps.individual.models import Individual
from apps.contribution_type.models import ContributionType


class PaymentForm(forms.ModelForm):
    """
    Form para sa Payment model.
    """
    # Gihimo natong dili required ang Individual sa form
    # kay basin wala pa naka-enroll ang nagbayad (pero dapat naa gyud sa sistema).
    # Depende ni sa imong business logic.
    individual = forms.ModelChoiceField(
        queryset=Individual.objects.all(),
        label="Nagbayad (Payer)",
        required=True,  # Gihimo ni natong REQUIRED kay dapat naa gyud nagbayad
        help_text="Pangitaa o pili-a ang nagbayad.",
        empty_label="Pili og Nagbayad"
    )

    # Contribution Type field
    contribution_type = forms.ModelChoiceField(
        queryset=ContributionType.objects.all(),
        label="Tipo sa Kontribusyon",
        required=True,  # Gihimo ni natong REQUIRED
        empty_label="Pili og Tipo sa Kontribusyon"
    )

    class Meta:
        model = Payment
        # Iapil lang ang mga fields nga ang user ang mag-input o magpili
        fields = [
            'individual',
            'amount',
            'date_paid',
            'payment_method',
            'gcash_reference_number',
            'contribution_type',
            # 'status' - gi-handle na ni sa views based sa payment_method
            # 'or_number' - automatic na pud ni sa views
            # 'collected_by', 'validated_by', etc. - gi-handle pud ni sa views (current user)
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
            'individual': 'Nagbayad (Payer)',
            'amount': 'Kantidad',
            'date_paid': 'Petsa sa Bayad',
            'payment_method': 'Pamaagi sa Bayad',
            'gcash_reference_number': 'GCash Reference #',
            'contribution_type': 'Tipo sa Kontribusyon',
        }

    def clean(self):
        """
        Custom validation para sa GCash reference number.
        Kinahanglan gyud naa kung 'gcash' ang payment_method.
        """
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        gcash_reference_number = cleaned_data.get('gcash_reference_number')

        if payment_method == 'gcash' and not gcash_reference_number:
            self.add_error('gcash_reference_number',
                           "Kinahanglan ang GCash Reference Number kung GCash ang pamaagi sa pagbayad.")
        return cleaned_data


# Formset para sa Covered Members (multiple members per payment)
CoveredMemberFormSet = inlineformset_factory(
    Payment,           # Parent Model
    CoveredMember,     # Child Model
    fields=['individual', 'amount_covered'],  # Fields nga i-display sa formset
    extra=1,           # Initial empty forms
    can_delete=True,   # Allow deleting existing covered members
    widgets={
        'individual': forms.Select(attrs={'class': 'form-select rounded-md shadow-sm mt-1 block w-full'}),
        'amount_covered': forms.NumberInput(attrs={'class': 'form-input rounded-md shadow-sm mt-1 block w-full'})
    },
    labels={
        'individual': 'Miyembro nga Gi-cover',
        'amount_covered': 'Kantidad nga Gi-cover',
    }
)
