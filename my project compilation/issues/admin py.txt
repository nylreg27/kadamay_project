from django.contrib import admin
from .models import IssueReport

@admin.register(IssueReport)
class IssueReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'reporter', 'created_at', 'status')  # update these as per your model
    list_filter = ('priority', 'status', 'created_at')
    search_fields = ('title', 'description', 'reporter__username')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
