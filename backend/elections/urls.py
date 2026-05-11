from rest_framework.routers import DefaultRouter

from .views import CandidateViewSet, ElectionViewSet, MeasureOptionViewSet, RaceViewSet

router = DefaultRouter()
router.register('elections', ElectionViewSet, basename='election')
router.register('races', RaceViewSet, basename='race')
router.register('candidates', CandidateViewSet, basename='candidate')
router.register('measure-options', MeasureOptionViewSet, basename='measure-option')

urlpatterns = router.urls
