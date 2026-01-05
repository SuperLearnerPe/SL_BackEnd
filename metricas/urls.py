from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GestionViewSet

router = DefaultRouter()
router.register(r'management', GestionViewSet, basename='metricas-management')

urlpatterns = [
    path('', include(router.urls)),
]