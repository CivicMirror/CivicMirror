from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from .models import OfficialResult
from .serializers import OfficialResultSerializer


class OfficialResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OfficialResult.objects.select_related('race', 'candidate', 'measure_option')
    serializer_class = OfficialResultSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['race', 'result_type', 'is_winner']
    search_fields = ['race__office_title', 'candidate__name', 'source_url']
    ordering_fields = ['vote_count', 'vote_pct', 'certified_at']
    ordering = ['-vote_count']
