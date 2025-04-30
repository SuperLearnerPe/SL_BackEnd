from rest_framework.routers import DefaultRouter
from students.views import StudentsViewSet

router = DefaultRouter()

router.register('students',StudentsViewSet,basename = 'students')

urlpatterns = router.urls
