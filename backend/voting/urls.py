from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ExternalRaceTallyAPIView,
    ExternalRaceVoteCreateAPIView,
    MyVoteHistoryAPIView,
    RaceTallyAPIView,
    RaceVoteCreateAPIView,
)

router = DefaultRouter()

urlpatterns = [
    # Voting by old-backend PK (existing routes — keep for backward compat)
    path('races/<int:pk>/vote/', RaceVoteCreateAPIView.as_view(), name='race-vote'),
    path('races/<int:pk>/tally/', RaceTallyAPIView.as_view(), name='race-tally'),
    # Voting by CivicMirror-API external_race_id
    path('races/ext/<int:external_id>/vote/', ExternalRaceVoteCreateAPIView.as_view(), name='race-vote-external'),
    path('races/ext/<int:external_id>/tally/', ExternalRaceTallyAPIView.as_view(), name='race-tally-external'),
    path('users/me/votes/', MyVoteHistoryAPIView.as_view(), name='my-votes'),
]
