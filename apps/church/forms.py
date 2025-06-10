from django import forms
from .models import Church, District
from apps.individual.models import Individual


class ChurchForm(forms.ModelForm):
    class Meta:
        model = Church
        fields = ['name', 'address', 'district', 'is_active', 'in_charge']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['district'].queryset = District.objects.all()

        # For dropdowns, use queryset from DB
        self.fields['district'].queryset = District.objects.all()
        self.fields['district'].label_from_instance = lambda obj: obj.name

        self.fields['in_charge'].queryset = Individual.objects.filter(
            is_active_member=True)
        self.fields['in_charge'].label_from_instance = lambda obj: f"{obj.given_name} {obj.surname}"
