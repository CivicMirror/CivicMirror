from django.contrib import admin

from .models import OfficialResult


@admin.register(OfficialResult)
class OfficialResultAdmin(admin.ModelAdmin):
    list_display = ('race', 'result_label', 'vote_count', 'vote_pct', 'is_winner', 'result_type', 'certified_at')
    search_fields = ('race__office_title', 'candidate__name', 'measure_option__option_label', 'source_url')
    list_filter = ('result_type', 'is_winner')
    autocomplete_fields = ('race', 'candidate', 'measure_option')
    readonly_fields = ('raw_payload',)

    @admin.display(description='Candidate / Option')
    def result_label(self, obj):
        if obj.is_write_in_aggregate:
            return 'Write-in (aggregate)'
        if obj.candidate:
            return obj.candidate.name
        if obj.measure_option:
            return obj.measure_option.option_label
        return '—'
