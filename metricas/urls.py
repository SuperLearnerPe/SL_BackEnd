from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MetricasViewSet

router = DefaultRouter()
router.register(r'metricas', MetricasViewSet, basename='metricas')

urlpatterns = [
    path('', include(router.urls)),
]