# apps/payment/forms.py

from django import forms
from django.forms import inlineformset_factory
from .models import Payment, CoveredMember, ContributionType, Individual
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML
from django.urls import reverse_lazy
from django.utils.html import format_html
from django.db.models.functions import Coalesce
from django.db.models import Max
from decimal import Decimal
import datetime  # Import datetime module

# --- Payment Form ---


class PaymentForm(forms.ModelForm):
    # or_number field: We'll make this read-only and automatically generate it
    or_number = forms.CharField(
        label="Official Receipt No.",
        max_length=50,
        required=False,  # Not required on form submission, it's auto-generated
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    # Custom field to display family members for selection
    # This will be dynamically populated via JavaScript or adjusted for select2
    # individual = forms.ModelChoiceField(
    #     queryset=Individual.objects.all(),
    #     label="Payer (Family Head/Individual)",
    #     required=True,
    #     widget=forms.Select(attrs={'class': 'select2'}) # Add select2 class for styling
    # )

    class Meta:
        model = Payment
        fields = [
            'or_number', 'individual', 'church', 'contribution_type',
            'amount_paid', 'payment_method', 'gcash_reference_number',
            'status', 'date_paid', 'notes', 'cancellation_reason'
        ]
        widgets = {
            'date_paid': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'cancellation_reason': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Reason for cancellation'}),
            # Use a specific class for JS
            'individual': forms.Select(attrs={'class': 'select2-individual'}),
            # Use a specific class for JS
            'church': forms.Select(attrs={'class': 'select2-church'}),
            # Specific class
            'contribution_type': forms.Select(attrs={'class': 'select2-contribution-type'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Initialize crispy forms helper
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('or_number', css_class='form-group col-md-6 mb-0'),
                Column('individual', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('church', css_class='form-group col-md-6 mb-0'),
                Column('contribution_type',
                       css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('amount_paid', css_class='form-group col-md-4 mb-0'),
                Column('payment_method', css_class='form-group col-md-4 mb-0'),
                Column('gcash_reference_number',
                       css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('status', css_class='form-group col-md-6 mb-0'),
                Column('date_paid', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'notes',
            HTML('<h3 class="text-xl font-semibold mt-6 mb-3">Covered Members</h3>'),
            HTML('<div id="formset-container" class="space-y-4">'),
            # This is where the formset will be rendered dynamically
            HTML('</div>'),  # Close formset-container
            HTML(f'<button type="button" id="add-covered-member" class="btn btn-sm btn-primary mt-4">Add Covered Member</button>'),
            'cancellation_reason',  # Add this field to the layout
            Submit('submit', 'Save Payment', css_class='btn btn-success mt-4')
        )

        # Set initial values for new payment forms
        if not self.instance.pk:
            # Generate OR number only for new payments
            today_str = datetime.date.today().strftime('%Y%m%d')
            last_or_number = Payment.objects.aggregate(Max('or_number'))[
                'or_number__max']

            if last_or_number and last_or_number.startswith(today_str):
                # If OR numbers exist for today, increment the last one
                try:
                    last_sequence = int(last_or_number[len(today_str):])
                    new_sequence = last_sequence + 1
                except ValueError:  # Fallback if sequence part is not an integer
                    new_sequence = 1
            else:
                # Start new sequence for today or if no previous OR exists
                new_sequence = 1

            # Ensure 4 digits for sequence
            self.fields['or_number'].initial = f"{today_str}{new_sequence:04d}"

            # Set default date_paid to today
            self.fields['date_paid'].initial = datetime.date.today()

            # Set collected_by if request user is available (assuming it's set in the view)
            # This might be handled better in the view's form_valid method or save_model
            # if self.request and self.request.user.is_authenticated:
            #     self.instance.collected_by = self.request.user

        # Conditionally hide gcash_reference_number based on payment_method
        # This will be primarily handled by JS, but good to have a backend default
        if self.instance and self.instance.payment_method != 'gcash':
            self.fields['gcash_reference_number'].widget.attrs['style'] = 'display:none;'
            self.fields['gcash_reference_number'].required = False

        # Hide cancellation_reason if not cancelled or if status is not 'cancelled'
        if self.instance and self.instance.status != 'cancelled':
            self.fields['cancellation_reason'].widget.attrs['style'] = 'display:none;'
            self.fields['cancellation_reason'].required = False

        # Make certain fields read-only for existing payments if needed (e.g., or_number after creation)
        if self.instance.pk:
            self.fields['or_number'].widget.attrs['readonly'] = 'readonly'
            # Not required for update
            self.fields['or_number'].required = False
            # Add other fields to be read-only on update if necessary

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        gcash_reference_number = cleaned_data.get('gcash_reference_number')
        status = cleaned_data.get('status')
        cancellation_reason = cleaned_data.get('cancellation_reason')

        if payment_method == 'gcash' and not gcash_reference_number:
            self.add_error('gcash_reference_number',
                           "G-Cash Reference Number is required for G-Cash payments.")

        if status == 'cancelled' and not cancellation_reason:
            self.add_error(
                'cancellation_reason', "Cancellation reason is required for cancelled payments.")

        # Add a check to ensure G-Cash reference number is NOT provided for cash payments
        if payment_method == 'cash' and gcash_reference_number:
            self.add_error('gcash_reference_number',
                           "G-Cash Reference Number should not be provided for Cash payments.")

        return cleaned_data


# --- Covered Member Form ---
class CoveredMemberForm(forms.ModelForm):
    # Add a pseudo-field for searching/selecting individuals for the formset
    # This will not be saved to the model directly, but used for UI
    member_search = forms.CharField(
        label="Search Member",
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'member-search-input', 'placeholder': 'Type to search members...'}),
        help_text=format_html('Start typing to search for family members. <a href="{}" target="_blank" class="text-blue-500">Add New Individual</a> if not found.',
                              # Link to add new individual
                              reverse_lazy('individual:individual_add_external'))
    )

    class Meta:
        model = CoveredMember
        fields = ['individual']  # Only the actual ForeignKey field
        widgets = {
            'individual': forms.HiddenInput(),  # Hide the actual individual field
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # Do not render <form> tags
        self.helper.disable_csrf = True  # CSRF is handled by the main form

        # Check if an instance exists and has an individual.
        # This prevents error when rendering empty forms in formset.
        if self.instance and self.instance.pk and self.instance.individual:  # ADDED `self.instance.pk` CHECK
            # If it's an existing instance with an individual, pre-fill member_search
            self.fields['member_search'].initial = self.instance.individual.full_name
            # And also set a data attribute on the hidden input for JS to pick up
            self.fields['individual'].widget.attrs['data-initial-id'] = self.instance.individual.pk
            self.fields['individual'].widget.attrs['data-initial-name'] = self.instance.individual.full_name

        self.helper.layout = Layout(
            Row(
                Column('member_search', css_class='form-group col-md-12 mb-0'),
                # Keep hidden
                Column('individual', css_class='form-group col-md-12 mb-0 d-none'),
            )
        )


# Covered Member Formset
CoveredMemberFormSet = inlineformset_factory(
    Payment,
    CoveredMember,
    form=CoveredMemberForm,
    extra=1,  # Number of empty forms to display initially
    can_delete=True,
    # You might want to limit the queryset for individual field if it was visible
    # fk_name='payment' # Specify the foreign key if there are multiple to Payment
)
