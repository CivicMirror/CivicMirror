from django.urls import include, path
from rest_framework.routers import DefaultRouter

from elections.urls import router as elections_router
from results.urls import router as results_router
from voting.urls import router as voting_router

router = DefaultRouter()
router.registry.extend(elections_router.registry)
router.registry.extend(results_router.registry)
router.registry.extend(voting_router.registry)

urlpatterns = [
    path('', include(router.urls)),
    path('', include('accounts.urls')),
]
