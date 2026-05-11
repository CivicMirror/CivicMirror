from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import MyVoteHistoryAPIView, RaceTallyAPIView, RaceVoteCreateAPIView

router = DefaultRouter()

urlpatterns = [
    path('races/<int:pk>/vote/', RaceVoteCreateAPIView.as_view(), name='race-vote'),
    path('races/<int:pk>/tally/', RaceTallyAPIView.as_view(), name='race-tally'),
    path('users/me/votes/', MyVoteHistoryAPIView.as_view(), name='my-votes'),
]
