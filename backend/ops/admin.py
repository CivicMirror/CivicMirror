from django.contrib import admin

from .models import SyncLog


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = (
        'task_name',
        'election',
        'status',
        'records_created',
        'records_updated',
        'error_count',
        'address_label',
        'started_at',
        'completed_at',
    )
    search_fields = ('task_name', 'source', 'address_label', 'last_error', 'election__name')
    list_filter = ('status', 'source', 'task_name', 'started_at', 'completed_at')
    autocomplete_fields = ('election',)
    readonly_fields = ('started_at', 'completed_at')
