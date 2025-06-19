# apps/payment/admin.py
from django.contrib import admin
from .models import Payment, CoveredMember, ContributionType

# Inline for Covered Members
class CoveredMemberInline(admin.TabularInline): # Use TabularInline for a compact display
    model = CoveredMember
    extra = 1 # Number of empty forms to display
    fields = ('individual', 'amount_allocated', 'notes')
    raw_id_fields = ('individual',) # Use raw_id_fields for Individual to handle many individuals better

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'receipt_number', 'date_paid', 'amount', 'payment_method',
        'get_payees_display', # Use the property from Payment model
        'payment_status', 'is_cancelled', 'collected_by', 'validated_by', 'created_at'
    )
    list_filter = ('payment_method', 'payment_status', 'is_cancelled', 'church', 'contribution_type')
    search_fields = ('receipt_number', 'notes', 'covered_members__individual__first_name', 'covered_members__individual__last_name')
    date_hierarchy = 'date_paid'
    ordering = ('-date_paid', '-receipt_number')

    inlines = [CoveredMemberInline] # Add the inline here

    fieldsets = (
        (None, {
            'fields': (
                'receipt_number', ('date_paid', 'amount'),
                ('payment_method', 'gcash_reference_number'),
                ('church', 'contribution_type'),
                'notes',
            ),
        }),
        ('People Involved', {
            'fields': ('collected_by', 'individual', 'deceased_member'), # individual and deceased_member can still be here if needed for direct assignment in admin
            'description': 'Select the primary individual or deceased member if applicable for this payment. Use "Payees / Covered Members" below for multiple individuals.',
            'classes': ('collapse',), # Collapse this section by default
        }),
        ('Validation & Cancellation', {
            'fields': (
                'payment_status', ('validated_by', 'validation_date'),
                'is_cancelled', ('cancellation_reason', 'cancellation_date', 'cancelled_by'),
            ),
            'classes': ('collapse',),
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at', 'is_legacy_record'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = (
        'created_at', 'updated_at', 'created_by', 'updated_by',
        'receipt_number', # This should be set by the system, not manually edited after creation
        'validated_by', 'validation_date', 'cancellation_date', 'cancelled_by'
    )

    # Automatically set created_by and updated_by when saving from admin
    def save_model(self, request, obj, form, change):
        if not obj.pk: # Only on creation
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Make collected_by default to the current user in admin if not set
        if not obj or not obj.collected_by:
            form.base_fields['collected_by'].initial = request.user
        return form

# Register the ContributionType model
@admin.register(ContributionType)
class ContributionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    ordering = ('name',)

