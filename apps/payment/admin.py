# apps/payment/admin.py

from django.contrib import admin
# IMPORTANT: Import PaymentIndividualAllocation
from .models import Payment, ContributionType, PaymentIndividualAllocation

# Inline for PaymentIndividualAllocation
# This allows you to add/edit individual allocations directly when editing a Payment


# Use TabularInline for a compact table layout
class PaymentIndividualAllocationInline(admin.TabularInline):
    model = PaymentIndividualAllocation
    extra = 1  # Number of empty forms to display
    # Assuming IndividualAdmin has search_fields
    autocomplete_fields = ['individual']


@admin.register(ContributionType)
class ContributionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'amount')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'receipt_number',  # <--- FIXED: Changed from 'receipt_no'
        'individual_display_name',
        'church',
        'contribution_type',
        'amount',
        'date_paid',
        'payment_status',
        'get_covered_members_display',
        'deceased_member_display_name',  # NEW: For the re-added deceased_member
    )
    list_filter = (
        'payment_status', 'payment_method', 'contribution_type', 'date_paid', 'church'
    )
    search_fields = (
        'receipt_number',  # <--- FIXED: Changed from 'receipt_no'
        'individual__surname', 'individual__given_name',
        # Updated for through model
        'covered_members__individual__surname', 'covered_members__individual__given_name',
        'deceased_member__surname', 'deceased_member__given_name',  # NEW: For deceased_member
    )
    autocomplete_fields = ('individual', 'church', 'contribution_type', 'collected_by', 'validated_by',
                           # Make sure all ForeignKeys that should use autocomplete are here
                           'cancelled_by', 'deceased_member',)

    # Add the inline here!
    # <--- NEW: This replaces covered_members in fieldsets
    inlines = [PaymentIndividualAllocationInline]

    # Fieldsets for better organization in the admin
    fieldsets = (
        ('Payment Details', {
            'fields': (
                'individual', 'church', 'contribution_type', 'amount', 'date_paid',
                # <-- deceased_member re-added here
                'payment_method', 'receipt_number', 'notes', 'deceased_member',
            )
        }),
        ('Payment Workflow & Audit', {
            'fields': (
                'payment_status', 'collected_by', 'validated_by', 'validation_date',
                'is_cancelled', 'cancellation_reason', 'cancelled_by', 'cancellation_date',
                'is_legacy_record',
                # 'covered_members', # <--- REMOVED: Managed by inline now
            ),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = (
        'created_at', 'updated_at', 'created_by', 'updated_by',
        'validation_date', 'validated_by',
        'cancellation_date', 'cancelled_by',
    )

    # Methods for list_display
    def individual_display_name(self, obj):
        return obj.individual.full_name if obj.individual else "N/A"
    individual_display_name.short_description = 'Payee'
    individual_display_name.admin_order_field = 'individual__surname'

    def get_covered_members_display(self, obj):
        # We now get covered members through the allocation model
        # You might want to display the allocated amount here too, e.g., "Juan (₱50), Pedro (₱50)"
        return ", ".join([f"{alloc.individual.full_name} (₱{alloc.allocated_amount})" for alloc in obj.individual_allocations.all()])
    get_covered_members_display.short_description = 'Covered Members'

    # NEW: Method for deceased_member display
    def deceased_member_display_name(self, obj):
        return obj.deceased_member.full_name if obj.deceased_member else "N/A"
    deceased_member_display_name.short_description = 'Deceased Member'
    deceased_member_display_name.admin_order_field = 'deceased_member__surname'
