# apps/family/forms.py
from django import forms
from .models import Family
from apps.church.models import Church
from apps.individual.models import Individual


class FamilyForm(forms.ModelForm):
    # NEW: This field will be used for displaying the name and for searching.
    # It's a CharField, not directly linked to the model's ForeignKey.
    # It will be populated by JavaScript.
    head_of_family_display = forms.CharField(
        label="Head of Family",
        required=False,  # It might be required for the model, but not directly for this display field
        help_text="Start typing to search for a member to be the Head of Family."
    )

    class Meta:
        model = Family
        # FIXED: Karon, 'head_of_family' kay i-handle na nato via JavaScript/hidden field.
        # So, dili na nato apilon sa 'fields' o i-exclude. Instead, ang custom field na ang gamiton.
        # Make sure 'contact_number' and 'is_active' are still included if they are model fields.
        fields = ['family_name', 'address',
                  'church', 'contact_number', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize head_of_family_display if an instance is provided (for editing)
        if self.instance and self.instance.head_of_family:
            self.fields['head_of_family_display'].initial = self.instance.head_of_family.full_name
            # Store the actual PK in a hidden field. This hidden field will be rendered manually in the template.
            # We will handle saving this in the view.

        # Apply DaisyUI/Tailwind classes to all fields
        for field_name, field in self.fields.items():
            if field_name == 'head_of_family_display':
                # Specific class for the search input field
                field.widget.attrs.update({
                    'class': 'input input-bordered w-full uppercase',
                    'id': 'id_head_of_family_display',  # Add an ID for JavaScript
                    'autocomplete': 'off',  # Prevent browser autocomplete
                    'placeholder': 'Search by name...'
                })
            elif isinstance(field.widget, (
                forms.TextInput,
                forms.Textarea,
                forms.EmailInput,
                forms.NumberInput,
                forms.DateInput
            )):
                # Default class for text-based inputs and date inputs
                field.widget.attrs.update(
                    {'class': 'input input-bordered w-full uppercase'})
            elif isinstance(field.widget, forms.Select):
                # Default class for select/dropdowns
                field.widget.attrs.update(
                    {'class': 'select select-bordered w-full uppercase'})
            elif isinstance(field.widget, forms.CheckboxInput):
                # Default class for checkboxes
                field.widget.attrs.update(
                    {'class': 'checkbox checkbox-primary'})

        # Custom handling for 'church' field
        # Keep this as is for now, assuming it's a standard dropdown
        if 'church' in self.fields:
            self.fields['church'].queryset = Church.objects.all().order_by(
                'name')
            self.fields['church'].empty_label = "Select Church"

        # Note: The actual model ForeignKey 'head_of_family' is not in 'fields' or 'exclude' here.
        # It will be handled in the FamilyCreateView/FamilyUpdateView based on the hidden input.
        # This makes the form not directly responsible for rendering the ForeignKey,
        # but for providing a display field and a hidden field for the actual ID.
