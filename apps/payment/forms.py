# apps/payment/forms.py

from django import forms
from django.forms import inlineformset_factory
from .models import Payment, PaymentIndividualAllocation, ContributionType, Individual
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, Field, HTML
# If needed for specific field styling
from crispy_forms.bootstrap import PrependedText, AppendedText


class PaymentForm(forms.ModelForm):
    # This field will be used for searching and selecting the primary individual.
    # It's not directly saved to the model, but used to populate the 'individual' ForeignKey.
    # We use a CharField here for a text input that will be populated by a JavaScript autocomplete/search.
    # The actual Individual object will be assigned in the view.
    primary_individual_search = forms.CharField(
        label="Search Primary Payer / Head of Family",
        required=False,  # Can be initially empty if no individual is pre-selected
        help_text="Start typing member's name or membership ID to search. This will be the primary payer for the OR.",
        widget=forms.TextInput(attrs={
                               'placeholder': 'Enter name or Membership ID...', 'class': 'input input-bordered w-full'}),
    )

    class Meta:
        model = Payment
        # Define the fields you want in your payment form.
        # receipt_number will be auto-generated or manually entered.
        # gcash_reference_number will be conditionally shown/required.
        fields = [
            'date_paid', 'amount', 'payment_method', 'gcash_reference_number',
            'notes', 'individual', 'church', 'contribution_type',
            'is_legacy_record', 'receipt_number', 'deceased_member'
        ]
        labels = {
            # Clarify this field's role
            'individual': 'Primary Payer (for OR)',
            'date_paid': 'Payment Date',
            'amount': 'Total Amount',
            'payment_method': 'Method',
            'notes': 'Remarks',
            'church': 'Church',
            'contribution_type': 'Contribution Type',
            'is_legacy_record': 'Is Legacy Record?',
            'receipt_number': 'Official Receipt No.',
            'deceased_member': 'Payment for Deceased Member',
            'gcash_reference_number': 'GCash Reference No.',
        }
        widgets = {
            'date_paid': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered w-full'}),
            'amount': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'textarea textarea-bordered w-full'}),
            # Initially hidden, will be populated by JS
            'individual': forms.Select(attrs={'class': 'select select-bordered w-full hidden'}),
            'church': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'contribution_type': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'receipt_number': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Auto-generated or enter manually'}),
            'is_legacy_record': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary'}),
            'deceased_member': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'gcash_reference_number': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Enter GCash transaction ID'}),
        }

    def __init__(self, *args, **kwargs):
        # individual_instance is passed when editing or creating for a specific individual
        self.individual_instance = kwargs.pop('individual_instance', None)
        super().__init__(*args, **kwargs)

        # Set initial value for primary_individual_search if an individual_instance is provided
        if self.individual_instance:
            self.fields[
                'primary_individual_search'].initial = f"{self.individual_instance.full_name} ({self.individual_instance.membership_id})"
            self.fields['individual'].initial = self.individual_instance.pk

        # Disable the direct individual field, it's managed by the search input + JS
        self.fields['individual'].widget.attrs['disabled'] = 'disabled'
        # Make it not required at form level (will be handled in view)
        self.fields['individual'].required = False

        # Crispy Forms Helper for layout and styling
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        # Add 'payment-form' ID for JS interaction
        self.helper.attrs = {'id': 'paymentForm'}

        # Define the layout using Crispy Forms with Tailwind/DaisyUI classes
        self.helper.layout = Layout(
            # Primary Payer / OR Details Section
            Fieldset(
                'PRIMARY PAYER & OR DETAILS',  # Fieldset title
                HTML('<hr class="my-4 border-base-200">'),  # Separator
                Row(
                    Column(
                        # Search input for primary payer
                        Field('primary_individual_search', css_class='mb-4'),
                        # Hidden field for actual individual FK
                        HTML(
                            '<input type="hidden" name="individual" id="id_individual" value="{{ form.individual.value|default:"" }}">'),
                        css_class='form-control col-span-12 md:col-span-6 mb-4'
                    ),
                    Column(
                        'date_paid',
                        css_class='form-control col-span-12 md:col-span-6 mb-4'
                    ),
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-4'
                ),
                Row(
                    Column(
                        'amount', css_class='form-control col-span-12 md:col-span-4 mb-4'),
                    Column(
                        'payment_method', css_class='form-control col-span-12 md:col-span-4 mb-4'),
                    Column(
                        # Initially hidden
                        Field('gcash_reference_number',
                              css_class='hidden gcash-field'),
                        css_class='form-control col-span-12 md:col-span-4 mb-4',
                        css_id='gcash_reference_number_column'  # ID for JS manipulation
                    ),
                    css_class='grid grid-cols-1 md:grid-cols-3 gap-4'
                ),
                Row(
                    Column(
                        'contribution_type', css_class='form-control col-span-12 md:col-span-6 mb-4'),
                    Column(
                        'church', css_class='form-control col-span-12 md:col-span-6 mb-4'),
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-4'
                ),
                Row(
                    Column(
                        'receipt_number', css_class='form-control col-span-12 md:col-span-6 mb-4'),
                    # Align checkbox
                    Column(
                        'is_legacy_record', css_class='form-control col-span-12 md:col-span-6 flex items-center pt-8 mb-4'),
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-4'
                ),
                'notes',
                'deceased_member',
                # Card styling for fieldset
                css_class='card bg-base-100 shadow-lg p-6 rounded-lg mb-6'
            ),

            # Allocation Fieldset (for formset) - This will be added in the template manually via the formset
            # We add a placeholder here for clarity, but the formset will render its own fields.
            HTML('<div id="allocation-formset-container" class="card bg-base-100 shadow-lg p-6 rounded-lg mb-6"></div>'),

            Submit('submit', 'CREATE PAYMENT',
                   css_class='btn btn-primary mt-6 uppercase')
        )

        # Make individual field required only if it's explicitly given a value (e.g., from search)
        self.fields['individual'].required = False

        # Conditional logic for gcash_reference_number
        if self.initial.get('payment_method') == 'GCASH' or self.data.get('payment_method') == 'GCASH':
            self.fields['gcash_reference_number'].required = True
            # Show it
            self.fields['gcash_reference_number'].widget.attrs['class'] += ' block'
            self.helper.layout.get_field(
                'gcash_reference_number').add_class('block')
            self.helper.layout.get_field('gcash_reference_number').remove_class(
                'hidden')  # Ensure it's not hidden by Crispy
        else:
            self.fields['gcash_reference_number'].required = False
            # Hide it
            self.fields['gcash_reference_number'].widget.attrs['class'] += ' hidden'
            self.helper.layout.get_field('gcash_reference_number').add_class(
                'hidden')  # Ensure hidden by Crispy
            self.helper.layout.get_field(
                'gcash_reference_number').remove_class('block')

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        gcash_reference_number = cleaned_data.get('gcash_reference_number')
        is_legacy_record = cleaned_data.get('is_legacy_record')
        receipt_number = cleaned_data.get('receipt_number')
        # This is the actual ForeignKey field value
        individual_fk = cleaned_data.get('individual')

        # Validate gcash_reference_number if payment_method is GCASH
        if payment_method == 'GCASH' and not gcash_reference_number:
            self.add_error('gcash_reference_number',
                           'GCash Reference Number is required for GCash payments.')

        # Validate that if not legacy, a receipt number is provided or will be auto-generated
        if not is_legacy_record:
            if not receipt_number and not self.instance:  # If new payment and not legacy, and no receipt number
                # It will be auto-generated in save, but we can ensure it's not explicitly empty if expected
                pass  # The model's save method handles auto-generation
            elif receipt_number:
                # Basic format validation for YY-NNNN if manually provided and not legacy
                if not re.fullmatch(r'^\d{2}-\d{4}$', receipt_number):
                    self.add_error(
                        'receipt_number', 'Receipt number must be in YY-NNNN format (e.g., 25-0001) or left blank for auto-generation.')

        # Ensure individual (FK) is provided, especially since the field is hidden
        # This will be validated by the view or during initial form processing.
        # If no instance provided and no individual selected
        if not individual_fk and not self.individual_instance:
            self.add_error('primary_individual_search',
                           'Please select a primary payer from the search results.')
            # If the individual field is required by the model and no value is passed, Django will complain.
            # So ensure the individual field is set to null=True in model or handled in view
            # The 'individual' FK is actually passed via a hidden input, so it will be in cleaned_data

        return cleaned_data


# Inline Formset for PaymentIndividualAllocation
# We will dynamically add/remove forms using JavaScript
PaymentIndividualAllocationFormSet = inlineformset_factory(
    Payment,
    PaymentIndividualAllocation,
    fields=['individual', 'allocated_amount', 'is_payer'],
    extra=1,  # Start with one empty form
    can_delete=True,  # Allow deleting allocations
    widgets={
        'individual': forms.Select(attrs={'class': 'select select-bordered w-full individual-allocation-select'}),
        'allocated_amount': forms.NumberInput(attrs={'class': 'input input-bordered w-full allocated-amount-input', 'step': '0.01'}),
        'is_payer': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary is-payer-checkbox'}),
    }
)

# Customizing the formset forms for Crispy Forms


class BasePaymentIndividualAllocationFormSet(forms.BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        form.fields['individual'].label = "Allocated To"
        form.fields['allocated_amount'].label = "Amount"
        form.fields['is_payer'].label = "Is Payer?"
        # Add crispy helper for each form in the formset
        form.helper = FormHelper()
        form.helper.form_show_labels = True
        form.helper.layout = Layout(
            Row(
                Column('individual', css_class='col-span-12 md:col-span-4'),
                Column('allocated_amount', css_class='col-span-12 md:col-span-3'),
                # Align checkbox
                Column(
                    'is_payer', css_class='col-span-12 md:col-span-2 pt-6 flex items-center'),
                # Delete checkbox
                Column(
                    'DELETE', css_class='col-span-12 md:col-span-2 pt-6 flex items-center'),
                # Use 12-column grid for flexibility
                css_class='grid grid-cols-1 md:grid-cols-12 gap-4 items-end mb-4'
            )
        )


# Create the actual formset factory with the custom base formset
PaymentIndividualAllocationFormSet = inlineformset_factory(
    Payment,
    PaymentIndividualAllocation,
    formset=BasePaymentIndividualAllocationFormSet,  # Use our custom base formset
    fields=['individual', 'allocated_amount', 'is_payer'],
    extra=1,
    can_delete=True,
    widgets={
        'individual': forms.Select(attrs={'class': 'select select-bordered w-full individual-allocation-select'}),
        'allocated_amount': forms.NumberInput(attrs={'class': 'input input-bordered w-full allocated-amount-input', 'step': '0.01'}),
        'is_payer': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary is-payer-checkbox'}),
    }
)
