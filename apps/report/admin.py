from django.contrib import admin
from .models import ReportLog

@admin.register(ReportLog)
class ReportLogAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'generated_by', 'church', 'timestamp')
    list_filter = ('report_type', 'church')
    search_fields = ('generated_by__username', 'church__name')
    date_hierarchy = 'timestamp'
    autocomplete_fields = ('generated_by', 'church')
    readonly_fields = ('timestamp',)