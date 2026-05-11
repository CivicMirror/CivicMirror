from rest_framework.routers import DefaultRouter

from .views import OfficialResultViewSet

router = DefaultRouter()
router.register('results', OfficialResultViewSet, basename='official-result')

urlpatterns = router.urls
