from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from knox.auth import TokenAuthentication
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from elections.models import Candidate, MeasureOption, Race

from .models import MockVote
from .serializers import MockVoteResponseSerializer, VoteCastRequestSerializer, VoteHistorySerializer
from .services import build_tally_payload


class VotingAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    @staticmethod
    def error_response(code: str, detail: str, status_code: int) -> Response:
        return Response({'code': code, 'detail': detail}, status=status_code)


class RaceVoteCreateAPIView(VotingAPIView):
    def post(self, request, pk: int):
        if not request.user or not request.user.is_authenticated:
            return self.error_response('not_authenticated', 'Authentication credentials were not provided.', status.HTTP_401_UNAUTHORIZED)

        payload = VoteCastRequestSerializer(data=request.data)
        if not payload.is_valid():
            return self.error_response('invalid_option', 'Provide exactly one valid option for this race.', status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            race = get_object_or_404(Race.objects.select_for_update(), pk=pk)
            if race.race_status != Race.RaceStatus.ACTIVE:
                return self.error_response('race_inactive', 'This race is not active.', status.HTTP_400_BAD_REQUEST)

            now = timezone.now()
            if not race.voting_opens or not race.voting_closes or not (race.voting_opens <= now <= race.voting_closes):
                return self.error_response('voting_closed', 'Voting is closed for this race.', status.HTTP_400_BAD_REQUEST)

            candidate = None
            measure_option = None
            candidate_id = payload.validated_data.get('candidate_id')
            measure_option_id = payload.validated_data.get('measure_option_id')

            if candidate_id is not None:
                candidate = Candidate.objects.filter(pk=candidate_id, race=race).first()
                if candidate is None:
                    return self.error_response('invalid_option', 'The selected option does not belong to this race.', status.HTTP_400_BAD_REQUEST)
            else:
                measure_option = MeasureOption.objects.filter(pk=measure_option_id, race=race).first()
                if measure_option is None:
                    return self.error_response('invalid_option', 'The selected option does not belong to this race.', status.HTTP_400_BAD_REQUEST)

            if MockVote.objects.filter(user=request.user, race=race).exists():
                return self.error_response('already_voted', 'You have already voted in this race.', status.HTTP_409_CONFLICT)

            try:
                vote = MockVote.objects.create(
                    user=request.user,
                    race=race,
                    candidate=candidate,
                    measure_option=measure_option,
                )
            except IntegrityError:
                return self.error_response('already_voted', 'You have already voted in this race.', status.HTTP_409_CONFLICT)

        return Response(MockVoteResponseSerializer(vote).data, status=status.HTTP_201_CREATED)


class RaceTallyAPIView(VotingAPIView):
    def get(self, request, pk: int):
        race = get_object_or_404(Race.objects.prefetch_related('candidates', 'measure_options'), pk=pk)
        return Response(build_tally_payload(race), status=status.HTTP_200_OK)


class MyVoteHistoryAPIView(VotingAPIView):
    def get(self, request):
        if not request.user or not request.user.is_authenticated:
            return self.error_response('not_authenticated', 'Authentication credentials were not provided.', status.HTTP_401_UNAUTHORIZED)

        queryset = MockVote.objects.select_related('race', 'race__election', 'candidate', 'measure_option').filter(user=request.user)
        return Response(VoteHistorySerializer(queryset, many=True).data, status=status.HTTP_200_OK)
