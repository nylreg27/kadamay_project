# apps/payment/forms.py

from django import forms
# Make sure you import PaymentIndividualAllocation if you will use it directly in the form later
from .models import Payment, ContributionType
from apps.individual.models import Individual
from django.forms.widgets import DateInput, NumberInput, TextInput, Select, Textarea


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
            attrs={'class': 'select select-bordered select-sm w-full'})
    )

    # RE-ADDED: Deceased Member field
    deceased_member = forms.ModelChoiceField(
        queryset=Individual.objects.filter(
            is_alive=False).order_by('surname', 'given_name'),
        empty_label="--- Select Deceased Member for Remarks ---",
        label="Remarks (Deceased Member)",
        required=False,
        widget=Select(
            attrs={'class': 'select select-bordered select-sm w-full'})
    )

    class Meta:
        model = Payment
        fields = [
            'individual',
            'contribution_type',
            'amount',
            'date_paid',
            'payment_method',
            'receipt_number',  # <-- Still 'receipt_number' not 'receipt_no'
            'deceased_member',  # <-- RE-ADDED to fields
            'notes',
        ]
        widgets = {
            'contribution_type': Select(attrs={'class': 'select select-bordered select-sm w-full'}),
            'amount': NumberInput(attrs={'class': 'input input-bordered input-sm w-full', 'placeholder': 'Enter amount'}),
            'date_paid': DateInput(attrs={'type': 'date', 'class': 'input input-bordered input-sm w-full'}),
            'payment_method': Select(attrs={'class': 'select select-bordered select-sm w-full'}),
            # <-- Still 'receipt_number'
            'receipt_number': TextInput(attrs={'class': 'input input-bordered input-sm w-full', 'placeholder': 'e.g., OR-00123'}),
            'notes': Textarea(attrs={'class': 'textarea textarea-bordered textarea-sm w-full'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contribution_type'].queryset = ContributionType.objects.all(
        ).order_by('name')

        # RE-ADDED: Initial value for deceased_member
        if self.instance and self.instance.pk and self.instance.deceased_member:
            self.fields['deceased_member'].initial = self.instance.deceased_member.id
