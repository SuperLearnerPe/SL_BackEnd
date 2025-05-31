from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MetricasViewSet, ImpactoViewSet, GestionViewSet

router = DefaultRouter()
router.register(r'metricas', MetricasViewSet, basename='metricas')
router.register(r'impacto', ImpactoViewSet, basename='impacto')
router.register(r'gestion', GestionViewSet, basename='gestion')

urlpatterns = [
    path('', include(router.urls)),
]