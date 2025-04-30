from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ParentsViewSet  # Importa solo ParentsViewSet

router = DefaultRouter()
router.register(r'parents', ParentsViewSet, basename='parents')  # Registra solo ParentsViewSet

urlpatterns = [
    path('', include(router.urls)),
]