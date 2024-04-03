from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg import openapi
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from django.urls import re_path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.views.generic import TemplateView

schema_view = get_schema_view(
    openapi.Info(
        title="LOCKER APIs",
        default_version="v1",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
urlpatterns = [
    re_path(r"^swagger$", 
schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('Privacy_policy.html', TemplateView.as_view(template_name='Privacy_policy.html')),
    path('Refund.html', TemplateView.as_view(template_name='Refund.html')),
    path('Prohibited_privacy.html', TemplateView.as_view(template_name='Prohibited_privacy.html')),
    path('Terms.html', TemplateView.as_view(template_name='Terms.html')),
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/', admin.site.urls),
    path('api/', include('storage_locker.urls')), 
    path('api/', include('users.urls')),
    path('api/', include('payments.urls')),
    path('control/', include('controlpanel.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

