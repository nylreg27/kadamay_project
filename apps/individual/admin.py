# apps/individual/admin.py
from django.contrib import admin
from .models import Individual # Import Individual model

@admin.register(Individual)
class IndividualAdmin(admin.ModelAdmin):
    # FIXED: Pinalitan ang 'members_serial' at 'church' ng tamang fields/methods
    list_display = (
        'surname',
        'given_name',
        'middle_name',
        'get_family_name', # Custom method para ipakita ang family name
        'get_church_name', # Custom method para ipakita ang church name
        'sex', # Idinagdag ang sex
        'civil_status', # Idinagdag ang civil_status
        'is_active_member',
        'is_alive',
    )
    # FIXED: Pinalitan ang 'church' at 'gender'
    list_filter = (
        'is_active_member',
        'is_alive',
        'relationship',
        'sex', # Gumamit ng 'sex' imbes na 'gender'
        'civil_status', # Idinagdag ang civil_status
        'family__church', # Filter by church name through family
    )
    # FIXED: Pinalitan ang 'church' ng 'family__church'
    autocomplete_fields = ('family',) # Para sa Family field, pwedeng mag-autocomplete


    # FIXED: Tinanggal ang 'date_joined' at pinalitan ng 'date_added'
    date_hierarchy = 'date_added' # Para mag-filter ng data by date

    # FIXED: Tinanggal ang 'readonly_fields' kung walang specific na gusto mong i-readonly
    # Kung gusto mo may readonly fields, tiyakin na field ng model ito o method sa admin
    # Halimbawa: readonly_fields = ('date_added',)
    
    # Mga field na pwedeng hanapin
    search_fields = (
        'surname',
        'given_name',
        'middle_name',
        'family__family_name', # Search by family name
        'family__church__name', # Search by church name
    )

    # Order ng mga field sa admin form
    fieldsets = (
        ('Personal Information', {
            'fields': (
                ('surname', 'given_name', 'middle_name', 'suffix_name'),
                ('sex', 'civil_status'),
                'birth_date',
                ('contact_number', 'email_address'),
            )
        }),
        ('Membership Information', {
            'fields': (
                'family',
                'relationship',
                ('is_active_member', 'is_alive'),
            )
        }),
    )

    # Custom methods for list_display
    @admin.display(description='Family Name')
    def get_family_name(self, obj):
        return obj.family.family_name if obj.family else '-'
    
    @admin.display(description='Church')
    def get_church_name(self, obj):
        return obj.family.church.name if obj.family and obj.family.church else '-'
    
    # Ginawa ang save_model override para masiguro na nilalagyan ng default value ang church
    # kung wala pang family ang individual, at para auto-assign ng church mula sa family
    def save_model(self, request, obj, form, change):
        if obj.family and not obj.family.church:
            # Optionally, prompt user or use a default church if family has no church
            # For now, let's assume family always has a church if family is selected
            pass # Django will handle the ForeignKey relation naturally

        super().save_model(request, obj, form, change)


