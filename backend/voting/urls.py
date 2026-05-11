from rest_framework.routers import DefaultRouter

from .views import MockVoteViewSet

router = DefaultRouter()
router.register('votes', MockVoteViewSet, basename='vote')

urlpatterns = router.urls
