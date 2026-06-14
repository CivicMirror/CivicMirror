from rest_framework.routers import SimpleRouter

from elections.views import CandidateViewSet, ElectionViewSet, MeasureOptionViewSet, RaceViewSet

router = SimpleRouter()
router.register('elections', ElectionViewSet, basename='v1-election')
router.register('races', RaceViewSet, basename='v1-race')
router.register('candidates', CandidateViewSet, basename='v1-candidate')
router.register('measure-options', MeasureOptionViewSet, basename='v1-measure-option')

urlpatterns = router.urls
