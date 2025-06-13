# apps/individual/admin.py

from django.contrib import admin
from .models import Individual


@admin.register(Individual)
class IndividualAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'membership_id',  # Changed from 'code' to 'membership_id'
        'full_name',
        'relationship',
        'sex',             # Added 'sex'
        'civil_status',    # Added 'civil_status'
        'is_alive',
        'is_active_member',
        'membership_status',
        'family',          # Good to display the family
        'date_added',      # Good to display date added
    )
    list_filter = (
        'is_alive',
        'is_active_member',
        'relationship',
        'membership_status',
        'sex',             # Added 'sex' filter
        'civil_status',    # Added 'civil_status' filter
        'family',          # Filter by family
        'family__church',  # Filter by church through family
    )
    search_fields = (
        'given_name',
        'surname',
        'middle_name',
        'suffix_name',      # Added suffix_name to search
        'membership_id',    # Changed from 'code' to 'membership_id'
        'contact_number',   # Added contact_number to search
        'email_address',    # Added email_address to search
        'address',          # Added individual's own address to search
        'family__family_name',  # Search by related family name
        'family__church__name',  # Search by related church name
    )

    date_hierarchy = 'date_added'  # Uncommented as 'date_added' exists

    list_display_links = ('id', 'full_name',)

    fieldsets = (
        (None, {
            'fields': (
                ('given_name', 'middle_name', 'surname', 'suffix_name'),
                'membership_id',  # Changed from 'code' to 'membership_id'
                'family'
            )
        }),
        ('Personal Information', {  # Re-added this fieldset
            'fields': (
                ('sex', 'civil_status'),
                'birth_date',
                'contact_number',
                'email_address',
                'address',  # Added individual's own address
            )
        }),
        ('Membership Status', {  # Renamed from 'Status' for clarity
            # Included relationship here
            'fields': ('membership_status', 'is_active_member', 'is_alive', 'relationship')
        }),
        ('Timestamps', {  # New fieldset for date_added
            'fields': ('date_added',),
            'classes': ('collapse',),  # Optional: make it collapsible
        })
    )

    # Optional: If you want to make date_added read-only in admin
    readonly_fields = ('date_added',)
