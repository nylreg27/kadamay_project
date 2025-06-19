# apps/individual/forms.py
from django import forms
from .models import Individual  # Import sa imong Individual model
from apps.family.models import Family # Import sa Family model para sa queryset
from crispy_forms.helper import FormHelper
# Import sa gikinahanglang layout objects para sa Crispy Forms
from crispy_forms.layout import Layout, Row, Column, Fieldset, Field 


class IndividualForm(forms.ModelForm):
    class Meta:
        model = Individual
        # Gamita ang '__all__' para maapil tanang fields, unya i-hide/arrange gamit ang Crispy Forms
        fields = '__all__'
        widgets = {
            'membership_status': forms.HiddenInput(),  # Itago ang field gikan sa UI
            'birth_date': forms.DateInput(attrs={'type': 'date'}), # HTML5 date picker
            'date_registered': forms.DateInput(attrs={'type': 'date'}), # HTML5 date picker
            'address': forms.Textarea(attrs={'rows': 3}), # Specific widget para sa address
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize sa Crispy Forms Helper
        self.helper = FormHelper()
        # Importante: Pugngi ang Crispy Forms nga maghimo sa kaugalingon niyang <form> tag,
        # kay naa na man kini sa imong HTML template.
        self.helper.form_tag = False  
        # Ibutang ang klase sa kinatibuk-ang container div sa form para sa spacing
        self.helper.form_class = 'space-y-6' 

        # Kung naghimo og bag-ong instance, i-set ang default membership_status sa 'ACTIVE'
        # Kini nga logic gikuha gikan sa imong orihinal nga forms.py
        if not self.instance.pk:
            self.fields['membership_status'].initial = 'ACTIVE'

        # Family field: Itago kung naka-pre-populate na pinaagi sa initial data (e.g., pag-add gikan sa family detail page)
        # Kini nga logic gikuha gikan sa imong orihinal nga forms.py
        if 'family' in self.initial and self.initial['family']:
            self.fields['family'].widget = forms.HiddenInput()
            self.fields['family'].required = False
        else:
            # I-populate ang family dropdown para sa pagpili
            self.fields['family'].queryset = Family.objects.all().order_by('family_name')
            self.fields['family'].empty_label = "Select Family"

        # I-define ang layout sa imong form fields gamit ang Crispy Forms' Layout objects
        # Kini maoy mopuli sa imong manual Tailwind class application sa __init__
        self.helper.layout = Layout(
            # Unang Fieldset: Personal Details
            Fieldset(
                # Title sa fieldset with Feather icon (kinahanglan ang feather-icons.js sa template)
                '<i data-feather="user" class="w-5 h-5 text-primary mr-2"></i> Personal Details',
                # Row para sa name fields (first, middle, last, suffix)
                Row(
                    Column(Field('first_name'), css_class='form-group col-span-1'),
                    Column(Field('middle_name'), css_class='form-group col-span-1'),
                    Column(Field('last_name'), css_class='form-group col-span-1'),
                    Column(Field('suffix'), css_class='form-group col-span-1'),
                    # Tailwind grid classes para sa responsive layout sulod sa row
                    css_class='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4' 
                ),
                # Row para sa gender ug birth date
                Row(
                    Column(Field('gender'), css_class='form-group col-span-1'),
                    Column(Field('birth_date'), css_class='form-group col-span-1'),
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-4'
                ),
                # Row para sa civil status ug contact number
                Row(
                    Column(Field('civil_status'), css_class='form-group col-span-1'),
                    Column(Field('contact_number'), css_class='form-group col-span-1'),
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-4'
                ),
                # Row para sa address (mokawat sa tibuok gilapdon sa 2-column grid)
                Row(
                    Column(Field('address'), css_class='form-group md:col-span-2'), 
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-4'
                ),
                # I-apply ang Tailwind card/shadow styling sa tibuok container sa fieldset
                css_class='card bg-base-200 shadow-md rounded-lg p-6 mb-6'
            ),

            # Ikaduhang Fieldset: Membership ug Family Information
            Fieldset(
                # Title sa fieldset with Feather icon
                '<i data-feather="users" class="w-5 h-5 text-accent mr-2"></i> Membership & Family',
                # Row para sa family ug relationship
                Row(
                    Column(Field('family'), css_class='form-group col-span-1'),
                    Column(Field('relationship_to_head'), css_class='form-group col-span-1'),
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-4'
                ),
                # Row para sa membership status ug date registered
                Row(
                    Column(Field('membership_status'), css_class='form-group col-span-1'),
                    Column(Field('date_registered'), css_class='form-group col-span-1'),
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-4'
                ),
                # I-apply ang Tailwind card/shadow styling sa tibuok container sa fieldset
                css_class='card bg-base-200 shadow-md rounded-lg p-6'
            )
        )

        # I-apply ang common DaisyUI/Tailwind classes sa tanang form fields (Crispy Forms nagkinahanglan niini dinhi)
        # Kini nga loop nagsiguro nga ang tanang inputs, selects, ug textareas makakuha og consistent nga styling
        for field_name, field in self.fields.items():
            # I-apply ang base classes para sa text, number, email, date inputs
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.EmailInput, forms.DateInput)):
                field.widget.attrs.update({'class': 'input input-bordered w-full'})
            # I-apply ang base classes para sa select dropdowns
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'select select-bordered w-full'})
            # I-apply ang base classes para sa textareas
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'textarea textarea-bordered w-full'})
            # I-apply ang base classes para sa checkboxes
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'checkbox checkbox-primary'})
            # I-apply ang base classes para sa radio buttons
            elif isinstance(field.widget, forms.RadioSelect):
                field.widget.attrs.update({'class': 'radio radio-primary'})

            # Ibutang ang required indicator sa placeholder para sa required fields
            # Kini nagsiguro nga nahibal-an sa mga user kung unsang fields ang mandatory
            if field.required:
                if 'placeholder' in field.widget.attrs and not field.widget.attrs['placeholder'].endswith('*'):
                    field.widget.attrs['placeholder'] += ' *'
                elif 'placeholder' not in field.widget.attrs:
                    field.widget.attrs['placeholder'] = 'Required *' # Fallback kung walay placeholder
