from django.urls import path, include
from rest_framework.routers import DefaultRouter
from volunteers.views import VolunteersViewSet

router = DefaultRouter()
router.register(r'volunteers', VolunteersViewSet, basename='volunteers')

urlpatterns = [
    path('', include(router.urls)),
]
