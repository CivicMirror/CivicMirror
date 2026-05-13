from django.contrib import admin
from django.utils import timezone

from .models import Candidate, CommunityRace, DistrictRecord, Election, ElectionCycle, MeasureOption, Race


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'election_date', 'jurisdiction_level', 'state', 'status', 'source_id')
    search_fields = ('name', 'source_id', 'state')
    list_filter = ('jurisdiction_level', 'status', 'state', 'election_date')
    ordering = ('election_date', 'name')


@admin.register(ElectionCycle)
class ElectionCycleAdmin(admin.ModelAdmin):
    list_display = ('cycle_year', 'description', 'cycle_start', 'cycle_end')
    search_fields = ('=cycle_year', 'description')


@admin.register(Race)
class RaceAdmin(admin.ModelAdmin):
    list_display = (
        'office_title',
        'election',
        'race_type',
        'jurisdiction',
        'state',
        'source',
        'community_status',
        'race_status',
        'certification_status',
    )
    search_fields = ('office_title', 'jurisdiction', 'canonical_key', 'ocd_division_id')
    list_filter = ('race_type', 'source', 'community_status', 'race_status', 'certification_status', 'geography_scope')
    autocomplete_fields = ('election', 'submitter', 'reviewed_by')

    @admin.display(ordering='election__state')
    def state(self, obj):
        return obj.election.state


@admin.register(CommunityRace)
class CommunityRaceAdmin(admin.ModelAdmin):
    list_display = ('office_title', 'jurisdiction', 'community_status', 'submitted_at', 'submitter', 'moderator_notes')
    list_display_links = ('office_title',)
    list_editable = ('moderator_notes',)
    search_fields = ('office_title', 'jurisdiction', 'location_name', 'submitter__username')
    list_filter = ('community_status',)
    ordering = ('submitted_at',)
    autocomplete_fields = ('election', 'submitter', 'reviewed_by')
    readonly_fields = ('submitter', 'submitted_at', 'reviewed_at', 'reviewed_by')
    actions = ('approve_races', 'reject_races')
    fields = (
        'election',
        'race_type',
        'office_title',
        'jurisdiction',
        'location_name',
        'community_status',
        'race_status',
        'submitter',
        'submitted_at',
        'moderator_notes',
        'rejection_reason',
        'reviewed_at',
        'reviewed_by',
    )

    @admin.action(description='Approve selected community races')
    def approve_races(self, request, queryset):
        updated = queryset.update(
            community_status=Race.CommunityStatus.ACTIVE,
            race_status=Race.RaceStatus.ACTIVE,
            reviewed_at=timezone.now(),
            reviewed_by=request.user,
            rejection_reason='',
        )
        self.message_user(request, f'Approved {updated} community races.')

    @admin.action(description='Reject selected community races')
    def reject_races(self, request, queryset):
        updated = queryset.update(
            community_status=Race.CommunityStatus.REJECTED,
            reviewed_at=timezone.now(),
            reviewed_by=request.user,
            rejection_reason='Rejected during moderation review.',
        )
        self.message_user(request, f'Rejected {updated} community races.')


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


@admin.register(DistrictRecord)
class DistrictRecordAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'district_type', 'district_number', 'ocd_division_id', 'election_year_valid')
    search_fields = ('name', 'ocd_division_id', 'fips_code')
    list_filter = ('state', 'district_type', 'approximate', 'election_year_valid')
