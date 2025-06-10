from django.contrib import admin
from .models import ContributionType, Payment

@admin.register(ContributionType)
class ContributionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'description')
    search_fields = ('name', 'description')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('individual', 'contribution_type', 'amount', 'date_paid')
    list_filter = ('contribution_type', 'date_paid')
    search_fields = ('individual__surname', 'individual__given_name', 'individual__members_serial', 
                    'remarks')
    autocomplete_fields = ('individual', 'contribution_type')
    date_hierarchy = 'date_paid'