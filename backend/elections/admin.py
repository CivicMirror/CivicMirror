from django.contrib import admin

from .models import Candidate, Election, MeasureOption, Race


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'election_date', 'jurisdiction_level', 'state', 'status', 'source_id')
    search_fields = ('name', 'source_id', 'state')
    list_filter = ('jurisdiction_level', 'status', 'state', 'election_date')
    ordering = ('election_date', 'name')


@admin.register(Race)
class RaceAdmin(admin.ModelAdmin):
    list_display = (
        'office_title',
        'election',
        'race_type',
        'jurisdiction',
        'state',
        'source',
        'race_status',
        'certification_status',
    )
    search_fields = ('office_title', 'jurisdiction', 'canonical_key', 'ocd_division_id')
    list_filter = ('race_type', 'source', 'race_status', 'certification_status', 'geography_scope')
    autocomplete_fields = ('election', 'submitted_by')

    @admin.display(ordering='election__state')
    def state(self, obj):
        return obj.election.state


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'race', 'party', 'incumbent', 'candidate_status')
    search_fields = ('name', 'party', 'race__office_title')
    list_filter = ('incumbent', 'candidate_status', 'party')
    autocomplete_fields = ('race',)


@admin.register(MeasureOption)
class MeasureOptionAdmin(admin.ModelAdmin):
    list_display = ('option_label', 'race')
    search_fields = ('option_label', 'race__office_title')
    autocomplete_fields = ('race',)
