

from rest_framework.routers import DefaultRouter
from volunteers.views import VolunteersViewSet

router = DefaultRouter()

router.register('teachers',VolunteersViewSet,basename = 'teachers')

urlpatterns = router.urls
