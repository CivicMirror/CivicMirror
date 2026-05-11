from django.contrib import admin

from .models import OfficialResult


@admin.register(OfficialResult)
class OfficialResultAdmin(admin.ModelAdmin):
    list_display = ('race', 'candidate', 'measure_option', 'vote_count', 'vote_pct', 'certified_at')
    search_fields = ('race__office_title', 'candidate__name', 'source_url')
    list_filter = ('certified_at', 'race__certification_status', 'result_type', 'is_winner')
    autocomplete_fields = ('race', 'candidate', 'measure_option')
