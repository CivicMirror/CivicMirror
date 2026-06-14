from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from ops.views import commands_view

urlpatterns = [
    path('admin/commands/', admin.site.admin_view(commands_view), name='admin-commands'),
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/', include('api.urls')),
    path('api/v1/', include('api.v1_urls')),
]
