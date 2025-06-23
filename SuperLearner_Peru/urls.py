"""
URL configuration for SuperLearner_Peru project.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="SuperLearner Peru API",
      default_version='v1',
      description="API Documentation for SuperLearner Peru System",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="admin@superlearner.pe"),
      license=openapi.License(name="MIT License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('', include('frontend.urls')),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/',include('api.urls')),
    path('api/',include('students.urls')),
    path('api/',include('parents.urls')),
    path('volunteers/',include('volunteers.urls')),
    path('metricas/', include('metricas.urls')),
    path('', include('frontend.urls')),]
