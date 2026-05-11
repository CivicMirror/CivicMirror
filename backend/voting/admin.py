from django.contrib import admin

from .models import MockVote


@admin.register(MockVote)
class MockVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'race', 'cast_at')
    search_fields = ('user__username', 'race__office_title')
    list_filter = ('cast_at', 'race__race_type')
    autocomplete_fields = ('user', 'race', 'candidate', 'measure_option')
