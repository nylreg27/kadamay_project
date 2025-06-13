# apps/payment/admin.py

from django.contrib import admin
from .models import ContributionType, Payment
# Import Individual model for autocomplete setup (correctly imported)
from apps.individual.models import Individual

# Admin for ContributionType


@admin.register(ContributionType)
class ContributionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'description')
    search_fields = ('name',)
    list_filter = ('name',)  # Added list_filter here for consistency

# Admin for Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    # Corrected list_display to match actual fields in Payment model
    list_display = (
        'receipt_no',
        'individual_display_name',      # Custom method for the Payee
        'contribution_type',
        'amount',
        'date_paid',
        'payment_method',               # Added payment_method
        'get_covered_members_display',  # Custom method to show covered members
        # 'is_active', # REMOVED: This field does not exist in your Payment model
    )

    # Corrected list_filter to use existing fields
    list_filter = (
        'contribution_type',
        'payment_method',
        'date_paid',
        # 'is_active', # REMOVED: This field does not exist in your Payment model
        # 'deceased_member', # REMOVED: This field does not exist in your Payment model
    )

    # Corrected search_fields to allow searching by actual existing model fields
    search_fields = (
        'receipt_no',
        'individual__given_name',       # Allows searching by the payee's given name
        'individual__surname',          # Allows searching by the payee's surname
        'notes',                        # Use 'notes' for remarks
        'contribution_type__name',      # Search by contribution type name
        'covered_members__given_name',  # Search by covered member's given name
        'covered_members__surname',     # Search by covered member's surname
        # 'deceased_member__given_name', # REMOVED: Field does not exist
    )

    # Autocomplete fields: These are ForeignKey or ManyToMany fields.
    # Make sure that IndividualAdmin (in individual/admin.py) has 'search_fields' defined.
    autocomplete_fields = [
        'individual',   # For the Payee
        'covered_members'  # For the ManyToMany field of covered members
        # 'deceased_member', # REMOVED: This field does not exist
    ]

    # Optional: Read-only fields in the admin interface
    readonly_fields = ('created_at', 'updated_at')

    # Optional: Organize fields into sections in the admin form
    fieldsets = (
        (None, {
            'fields': (('individual', 'receipt_no'), 'date_paid', 'payment_method', 'contribution_type', 'amount', 'notes')
            # 'is_active' REMOVED from fields
        }),
        ('Covered Individuals', {
            'fields': ('covered_members',),  # This is your ManyToMany field
            'description': "Select other individuals covered by this payment.",
        }),
        # 'deceased_member' REMOVED from fieldsets
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)  # Makes this section collapsible
        }),
    )

    # --- Custom methods for list_display ---
    # This method gets the full name of the Individual who made the payment (Payee)
    def individual_display_name(self, obj):
        return obj.individual.full_name if obj.individual else "N/A"
    individual_display_name.short_description = 'Payee'  # Column header in admin list
    # Allows sorting by payee's surname
    individual_display_name.admin_order_field = 'individual__surname'

    # NEW: Method to display covered members in list_display
    def get_covered_members_display(self, obj):
        return ", ".join([member.full_name for member in obj.covered_members.all()])
    # Column header in admin list
    get_covered_members_display.short_description = 'Covered Members'


# --- IMPORTANT: FOR AUTOCOMPLETE_FIELDS TO WORK ---
# Siguraduhon nga ang imong IndividualAdmin sa apps/individual/admin.py naay
# 'search_fields' nga gi-define. Kung wala pa, ingon ani ang example:

# apps/individual/admin.py (EXAMPLE ONLY - DILI NI I-PASTE SA apps/payment/admin.py)
# from django.contrib import admin
# from .models import Individual, Family # Assuming Family is here too

# @admin.register(Individual)
# class IndividualAdmin(admin.ModelAdmin):
#    list_display = ('full_name', 'family', 'status')
#    search_fields = ('given_name', 'surname', 'membership_id') # KINI ANG CRUCIAL LINE
#    list_filter = ('status', 'family')

# @admin.register(Family)
# class FamilyAdmin(admin.ModelAdmin):
#    list_display = ('family_id', 'head_of_family', 'address')
#    search_fields = ('family_id', 'head_of_family__given_name', 'head_of_family__surname', 'address')
