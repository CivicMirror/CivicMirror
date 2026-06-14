from datetime import datetime, time

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from knox.auth import TokenAuthentication
from rest_framework import filters, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.utils import ensure_user_profile

from .models import Candidate, Election, MeasureOption, Race
from .serializers import (
    CandidateSerializer,
    CommunityRaceSubmissionSerializer,
    ElectionSerializer,
    MeasureOptionSerializer,
    RaceDetailSerializer,
    RaceSerializer,
    RaceSummarySerializer,
)
from .zip_utils import resolve_state_from_zip


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
    filterset_fields = ['race_type', 'source', 'race_status', 'certification_status', 'geography_scope', 'election', 'ballot_type']
    search_fields = ['office_title', 'jurisdiction', 'canonical_key', 'ocd_division_id']
    ordering_fields = ['office_title', 'last_synced_at']
    ordering = ['office_title']

    # Columns dropped from the production DB in later migrations but still defined in
    # the model (code diverged from production schema). Defer them to avoid SELECT errors.
    _DEFERRED_RACE_COLS = (
        'community_status', 'submitter_id', 'submitted_at',
        'moderator_notes', 'reviewed_at', 'reviewed_by_id', 'rejection_reason',
        'external_race_id',
    )

    def get_queryset(self):
        queryset = (
            Race.public_objects
            .defer(*self._DEFERRED_RACE_COLS)
            .select_related('election')
            .prefetch_related('candidates', 'measure_options')
        )

        scope = self.request.query_params.get('scope')
        state = self.request.query_params.get('state')
        zip_code = self.request.query_params.get('zip')
        election_id = self.request.query_params.get('election_id')

        if election_id:
            queryset = queryset.filter(election_id=election_id)

        if scope == 'national':
            queryset = queryset.filter(election__jurisdiction_level=Election.JurisdictionLevel.NATIONAL)
        elif scope == 'state':
            if not state:
                return queryset.none()
            queryset = queryset.filter(
                election__state=state.upper(),
                geography_scope__in=['statewide', 'district'],
            )
        elif scope == 'zip':
            if not zip_code:
                return queryset.none()
            resolved_state = resolve_state_from_zip(zip_code)
            if not resolved_state:
                return queryset.none()
            state_lower = resolved_state.lower()
            # Include races from national elections only when the race itself is
            # truly national (no state component in its OCD ID) or belongs to the
            # resolved state (OCD ID contains state:<xx>/ or ends with state:<xx>).
            national_and_relevant = Q(
                election__jurisdiction_level=Election.JurisdictionLevel.NATIONAL
            ) & (
                ~Q(ocd_division_id__icontains='state:')
                | Q(ocd_division_id__icontains=f'state:{state_lower}/')
                | Q(ocd_division_id__iendswith=f'state:{state_lower}')
            )
            queryset = queryset.filter(
                Q(election__state=resolved_state) | national_and_relevant
            )
        elif scope == 'address':
            # Address-based geocoding is not yet implemented.
            return queryset.none()
        elif scope is not None:
            # Unknown scope — return nothing rather than leaking all races.
            return queryset.none()
        elif state:
            # Backward-compatible: ?state=XX without a scope param.
            queryset = queryset.filter(
                election__state=state.upper(),
                geography_scope__in=['statewide', 'district'],
            )

        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RaceDetailSerializer
        return super().get_serializer_class()


class LocalRaceSubmissionAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    @staticmethod
    def error_response(code: str, detail: str, status_code: int) -> Response:
        return Response({'code': code, 'detail': detail}, status=status_code)

    @staticmethod
    def _community_election_defaults(election_date):
        return {
            'name': f'Community Local Election {election_date.isoformat()}',
            'election_date': election_date,
            'jurisdiction_level': Election.JurisdictionLevel.LOCAL,
            'status': Election.Status.UPCOMING,
        }

    @staticmethod
    def _build_voting_window(election_date):
        current_tz = timezone.get_current_timezone()
        voting_opens = timezone.make_aware(datetime.combine(election_date, time.min), current_tz)
        voting_closes = timezone.make_aware(datetime.combine(election_date, time.max), current_tz)
        return voting_opens, voting_closes

    def post(self, request):
        if not request.user or not request.user.is_authenticated:
            return self.error_response('not_authenticated', 'Authentication credentials were not provided.', status.HTTP_401_UNAUTHORIZED)

        serializer = CommunityRaceSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'detail': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        office_title = data['office_title'].strip() if data['race_type'] == Race.RaceType.CANDIDATE else data['question_title'].strip()
        jurisdiction = data.get('jurisdiction', '').strip() or data['location_name'].strip() or data.get('ballot_type', '').strip()
        conflicts = Race.objects.select_related('election').filter(
            office_title__iexact=office_title,
            jurisdiction=jurisdiction,
            election__election_date=data['election_date'],
        )
        if not data.get('force_submit') and conflicts.exists():
            return Response(
                {
                    'conflict': True,
                    'races': RaceSummarySerializer(conflicts, many=True).data,
                    'message': 'Similar races found. Confirm to submit anyway.',
                },
                status=status.HTTP_200_OK,
            )

        election, _ = Election.objects.get_or_create(
            source_id=f'community-local-{data["election_date"].isoformat()}',
            defaults=self._community_election_defaults(data['election_date']),
        )
        voting_opens, voting_closes = self._build_voting_window(data['election_date'])
        submitter = ensure_user_profile(request.user)

        with transaction.atomic():
            race = Race.objects.create(
                election=election,
                race_type=data['race_type'],
                office_title=office_title,
                jurisdiction=jurisdiction,
                geography_scope=data.get('jurisdiction', '').strip() or 'local',
                voting_opens=voting_opens,
                voting_closes=voting_closes,
                certification_status=Race.CertificationStatus.UPCOMING,
                source=Race.Source.COMMUNITY,
                community_status=Race.CommunityStatus.PENDING_REVIEW,
                submitter=submitter,
                submitted_at=timezone.now(),
                source_links=data.get('source_links', []),
                location_name=data['location_name'].strip(),
                race_status=Race.RaceStatus.PENDING_REVIEW,
                vote_method=Race.VoteMethod.SINGLE_CHOICE if data['race_type'] == Race.RaceType.CANDIDATE else Race.VoteMethod.YES_NO,
                ballot_type=data.get('ballot_type', '').strip(),
                yes_vote_details=data.get('yes_vote_details', '').strip(),
                no_vote_details=data.get('no_vote_details', '').strip(),
                supporting_links=data.get('supporting_links', []),
            )
            if data['race_type'] == Race.RaceType.CANDIDATE:
                Candidate.objects.bulk_create(
                    [
                        Candidate(
                            race=race,
                            name=candidate['name'].strip(),
                            party=candidate.get('party', '').strip(),
                            description=candidate.get('description', '').strip(),
                            image_url=candidate.get('image_url', ''),
                            website_url=candidate.get('website_url', ''),
                            candidate_status=candidate.get('candidate_type', Candidate.CandidateStatus.RUNNING),
                        )
                        for candidate in data.get('candidates', [])
                    ]
                )
            else:
                MeasureOption.objects.bulk_create(
                    [
                        MeasureOption(race=race, option_label='Yes'),
                        MeasureOption(race=race, option_label='No'),
                    ]
                )

        return Response({'id': race.id}, status=status.HTTP_201_CREATED)


class CandidateViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CandidateSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['race', 'candidate_status', 'incumbent', 'party']
    search_fields = ['name', 'party', 'race__office_title']

    def get_queryset(self):
        return Candidate.objects.select_related('race', 'race__election').filter(race__in=Race.public_objects.all())


class MeasureOptionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MeasureOptionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['race']
    search_fields = ['option_label', 'race__office_title']

    def get_queryset(self):
        return MeasureOption.objects.select_related('race', 'race__election').filter(race__in=Race.public_objects.all())
