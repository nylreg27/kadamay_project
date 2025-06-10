# apps/church/admin.py
from django.contrib import admin
from .models import District, Church # FIXED: Tinanggal ang UserChurch

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Church)
class ChurchAdmin(admin.ModelAdmin):
    list_display = ('name', 'district', 'in_charge', 'is_active')
    list_filter = ('is_active', 'district')
    search_fields = ('name', 'address')
