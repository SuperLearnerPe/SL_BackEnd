from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MetricasViewSet, ImpactoViewSet, GestionViewSet

router = DefaultRouter()
router.register(r'general', MetricasViewSet, basename='metricas-general')
router.register(r'impact', ImpactoViewSet, basename='metricas-impacto')
router.register(r'management', GestionViewSet, basename='metricas-gestion')

urlpatterns = [
    path('', include(router.urls)),
]