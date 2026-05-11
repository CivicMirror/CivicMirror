from django.urls import include, path
from rest_framework.routers import DefaultRouter

from elections.urls import router as elections_router, urlpatterns as elections_urlpatterns
from results.urls import router as results_router
from voting.urls import router as voting_router, urlpatterns as voting_urlpatterns

router = DefaultRouter()
router.registry.extend(elections_router.registry)
router.registry.extend(results_router.registry)
router.registry.extend(voting_router.registry)

urlpatterns = [
    path('', include((elections_urlpatterns, 'elections'))),
    path('', include((voting_urlpatterns, 'voting'))),
    path('', include('accounts.urls')),
    path('', include(router.urls)),
]
