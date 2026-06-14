from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from elections.sitemaps import RaceSitemap, StaticViewSitemap
from ops.views import commands_view

_sitemaps = {
    'static': StaticViewSitemap,
    'races': RaceSitemap,
}

urlpatterns = [
    path('admin/commands/', admin.site.admin_view(commands_view), name='admin-commands'),
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/', include('api.urls')),
    path('api/v1/', include('api.v1_urls')),
    path('sitemap.xml', sitemap, {'sitemaps': _sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]
