from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from elections.models import Race

from .models import OfficialResult
from .serializers import OfficialResultSerializer


class OfficialResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OfficialResult.objects.select_related('race', 'candidate', 'measure_option')
    serializer_class = OfficialResultSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['race', 'result_type', 'is_winner']
    search_fields = ['race__office_title', 'candidate__name', 'source_url']
    ordering_fields = ['round_number', 'vote_count', 'vote_pct', 'certified_at']
    ordering = ['round_number', '-vote_count', 'id']


class RaceOfficialResultsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk: int):
        race = get_object_or_404(Race.public_objects.select_related('election'), pk=pk)
        results = race.official_results.select_related('candidate', 'measure_option').order_by('round_number', '-vote_count', 'id')
        source_url = results.exclude(source_url='').values_list('source_url', flat=True).first() or ''
        return Response(
            {
                'race_id': race.id,
                'certification_status': race.certification_status,
                'source_url': source_url,
                'results': OfficialResultSerializer(results, many=True).data,
            }
        )
