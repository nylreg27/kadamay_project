# apps/payment/forms.py

from django import forms
from .models import Payment, ContributionType
from apps.individual.models import Individual  # Make sure this import is correct
from django.forms.widgets import DateInput, NumberInput, TextInput, Select, Textarea


class PaymentForm(forms.ModelForm):
    # Payee field: Only show individuals where relationship is 'HEAD' (all caps as per your DB screenshot)
    individual = forms.ModelChoiceField(
        queryset=Individual.objects.filter(
            is_active_member=True,
            is_alive=True,
            relationship='HEAD'  # <--- CRITICAL: Changed to 'HEAD' (all caps)
        ).order_by('surname', 'given_name'),
        empty_label="--- Select Payee (Head of Family) ---",
        label="Payee (Head of Family)",
        widget=Select(
            attrs={'class': 'select select-bordered select-sm w-full'})
    )

    # Deceased Member field: For remarks/deceased payments
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
            'receipt_no',
            'deceased_member',
            # 'notes', # Uncomment if you have a 'notes' field in your Payment model
        ]
        widgets = {
            'contribution_type': Select(attrs={'class': 'select select-bordered select-sm w-full'}),
            'amount': NumberInput(attrs={'class': 'input input-bordered input-sm w-full', 'placeholder': 'Enter amount'}),
            'date_paid': DateInput(attrs={'type': 'date', 'class': 'input input-bordered input-sm w-full'}),
            'payment_method': Select(attrs={'class': 'select select-bordered select-sm w-full'}),
            'receipt_no': TextInput(attrs={'class': 'input input-bordered input-sm w-full', 'placeholder': 'e.g., OR-00123'}),
            # 'notes': Textarea(attrs={'class': 'textarea textarea-bordered textarea-sm w-full'}), # Uncomment if you have a 'notes' field
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contribution_type'].queryset = ContributionType.objects.all(
        ).order_by('name')

        # Set initial value for deceased_member if editing an existing payment
        if self.instance and self.instance.pk and self.instance.deceased_member:
            self.fields['deceased_member'].initial = self.instance.deceased_member.id
