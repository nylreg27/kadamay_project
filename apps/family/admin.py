from django.contrib import admin

from .models import Family



@admin.register(Family)

class FamilyAdmin(admin.ModelAdmin):

    list_display = ('family_name', 'church', 'address', 'is_active')

    list_filter = ('church', 'is_active')

    search_fields = ('family_name', 'address')

    autocomplete_fields = ('church',) 
