from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import OfficialResultViewSet, RaceOfficialResultsAPIView

router = DefaultRouter()
router.register('results', OfficialResultViewSet, basename='official-result')

urlpatterns = [
    path('races/<int:pk>/official-results/', RaceOfficialResultsAPIView.as_view(), name='race-official-results'),
]
