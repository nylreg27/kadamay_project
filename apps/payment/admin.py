# apps/payment/admin.py

from django.contrib import admin
from .models import Payment, CoveredMember

# Register your models here.


class CoveredMemberInline(admin.TabularInline):
    """
    Inline admin for CoveredMember to be used within PaymentAdmin.
    Allows managing covered members directly from the Payment change form.
    """
    model = CoveredMember
    extra = 1  # Number of empty forms to display
    fields = ('individual',)  # The fields to display for each covered member


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Payment model.
    """
    list_display = (
        'or_number',
        'individual_full_name',  # Custom method to display payer's full name
        'amount_paid',          # Corrected from 'amount' to 'amount_paid'
        'payment_method',
        'status',
        'date_paid',
        'collected_by_username',  # Custom method to display collector's username
        'validated_by_username',  # Custom method to display validator's username
        'is_cancelled',          # Property from model
    )
    list_filter = (
        'payment_method',
        'status',
        'date_paid',
        'church',
        'contribution_type',
    )
    search_fields = (
        'or_number',
        'individual__first_name',
        'individual__last_name',
        'collected_by__username',
        'notes',
        'gcash_reference_number',  # Added for search
    )
    date_hierarchy = 'date_paid'  # Allows drilling down by date

    # Corrected readonly_fields
    readonly_fields = (
        'or_number',
        'created_at',
        'created_by',
        'updated_at',
        'updated_by',
        'validated_at',
        'cancelled_at',
    )

    # Fields that should be displayed in the form, in order
    fieldsets = (
        (None, {
            'fields': (
                'or_number',
                ('individual', 'church'),  # Group these in a row
                ('contribution_type', 'amount_paid'),  # Group these
                # Group payment method and Gcash ref
                ('payment_method', 'gcash_reference_number'),
                ('status', 'date_paid'),  # Group status and date
                'notes',
                'cancellation_reason',  # Add cancellation reason field
            )
        }),
        ('Audit Information', {
            'classes': ('collapse',),  # Makes this section collapsible
            'fields': (
                'created_at', 'created_by',
                'updated_at', 'updated_by',
                'collected_by',
                'validated_by', 'validated_at',
                'cancelled_by', 'cancelled_at',
            ),
        }),
    )

    inlines = [CoveredMemberInline]  # Link CoveredMember model here

    # Custom methods for list_display
    @admin.display(description='Payer')
    def individual_full_name(self, obj):
        return obj.individual.full_name if obj.individual else 'N/A'

    @admin.display(description='Collected By')
    def collected_by_username(self, obj):
        return obj.collected_by.username if obj.collected_by else 'N/A'

    @admin.display(description='Validated By')
    def validated_by_username(self, obj):
        return obj.validated_by.username if obj.validated_by else 'N/A'

    # Override save_model to automatically set created_by and updated_by
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only set created_by on creation
            obj.created_by = request.user
        obj.updated_by = request.user  # Always set updated_by on save
        super().save_model(request, obj, form, change)

# If you also need to register CoveredMember separately
# admin.site.register(CoveredMember)
