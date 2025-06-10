from django import forms
from .models import ContributionType, Payment

class ContributionTypeForm(forms.ModelForm):
    class Meta:
        model = ContributionType
        fields = ['name', 'description', 'amount']

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['individual', 'contribution_type', 'amount', 'date_paid', 'remarks']
        widgets = {
            'date_paid': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        contribution_type = self.cleaned_data.get('contribution_type')
        if amount and contribution_type and amount < contribution_type.amount:
            raise forms.ValidationError(
                f"Amount must be at least {contribution_type.amount} for this contribution type."
            )
        return amount