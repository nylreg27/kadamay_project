from django.contrib import admin
from .models import UserChurch
from .models import Profile


admin.site.register(Profile)

@admin.register(UserChurch)
class UserChurchAdmin(admin.ModelAdmin):
    list_display = ('user', 'church', 'role')
    list_filter = ('church',)  # Only real model fields here
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'church__name')
    autocomplete_fields = ('user', 'church')
