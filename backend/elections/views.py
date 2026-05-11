from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from .models import Candidate, Election, MeasureOption, Race
from .serializers import CandidateSerializer, ElectionSerializer, MeasureOptionSerializer, RaceSerializer


class ElectionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ElectionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['jurisdiction_level', 'state', 'status']
    search_fields = ['name', 'source_id', 'state']
    ordering_fields = ['election_date', 'name']
    ordering = ['election_date', 'name']

    def get_queryset(self):
        return Election.objects.annotate(race_count=Count('races')).all()


class RaceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RaceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['race_type', 'source', 'race_status', 'certification_status', 'geography_scope', 'election']
    search_fields = ['office_title', 'jurisdiction', 'canonical_key', 'ocd_division_id']
    ordering_fields = ['office_title', 'last_synced_at']
    ordering = ['office_title']

    def get_queryset(self):
        queryset = Race.objects.select_related('election', 'submitted_by').prefetch_related('candidates', 'measure_options')
        state = self.request.query_params.get('state')
        if state:
            queryset = queryset.filter(election__state=state.upper())
        return queryset


class CandidateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Candidate.objects.select_related('race', 'race__election')
    serializer_class = CandidateSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['race', 'candidate_status', 'incumbent', 'party']
    search_fields = ['name', 'party', 'race__office_title']


class MeasureOptionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MeasureOption.objects.select_related('race', 'race__election')
    serializer_class = MeasureOptionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['race']
    search_fields = ['option_label', 'race__office_title']
