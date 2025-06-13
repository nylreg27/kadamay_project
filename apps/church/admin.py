# apps/church/admin.py (Full and Corrected Version)

from django.contrib import admin
from .models import District, Church


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Church)
class ChurchAdmin(admin.ModelAdmin):
    list_display = ('name', 'district', 'in_charge', 'is_active')
    list_filter = ('is_active', 'district')
    # Added search fields for the in_charge user in the admin panel
    search_fields = ('name', 'address', 'in_charge__username',
                     'in_charge__first_name', 'in_charge__last_name')
