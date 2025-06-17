from django.contrib import admin
from django.utils.html import format_html

class IssueReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'reporter', 'priority', 'colored_status', 'created_at')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('title', 'reporter__username')
    autocomplete_fields = ('reporter',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    def colored_status(self, obj):
        color_map = {
            'Pending': 'red',
            'In Progress': 'orange',
            'Resolved': 'green',
        }
        color = color_map.get(obj.status, 'black')
        return format_html(
            '<strong style="color: {};">{}</strong>', color, obj.status
        )
    colored_status.short_description = 'Status'

    def bold_priority(self, obj):
        style = {
            'Low': 'color: gray;',
            'Medium': 'color: orange;',
            'High': 'color: red; font-weight: bold;',
        }
        css = style.get(obj.priority, '')
        return format_html('<span style="{}">{}</span>', css, obj.priority)

    bold_priority.short_description = 'Priority'
