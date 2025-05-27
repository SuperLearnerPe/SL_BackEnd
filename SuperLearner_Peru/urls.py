"""
URL configuration for SuperLearner_Peru project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import UserViewSet, ClassViewSset, StudentsViewset, SupportViewset
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# Configuración del esquema de API mejorado
schema_view = get_schema_view(
    openapi.Info(
        title="SuperLearner API",
        default_version='v1',
        description="""
## API del Sistema SuperLearner

Esta API proporciona acceso completo al sistema de gestión educativa SuperLearner.

### Autenticación
Todos los endpoints (excepto login y registro) requieren autenticación mediante token.

**Pasos para autenticarse:**
1. Obtén tu token usando el endpoint `/api/user/login/`
2. Incluye el token en el header Authorization: `Token <tu_token>`
3. Usa el botón "Authorize" arriba para configurar tu token

### Endpoints Principales
- **🔐 Autenticación**: Login, registro y gestión de usuarios
- **👤 Usuario**: Información de perfil de usuario
- **📚 Cursos**: Gestión de clases y cursos
- **👥 Estudiantes**: Gestión de estudiantes y asistencia
- **🛠️ Soporte**: Sistema de soporte técnico
        """,
        contact=openapi.Contact(name="Soporte SuperLearner", email="soporte@superlearner.com"),
        license=openapi.License(name="Privado"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[],
)

# Configuración del router
router = DefaultRouter()
router.register(r'user', UserViewSet, basename='user')
router.register(r'class', ClassViewSset, basename='class')  
router.register(r'student', StudentsViewset, basename='student')
router.register(r'support', SupportViewset, basename='support')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include(router.urls)),
    
    # Documentación de API mejorada
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Endpoint de documentación principal
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),
]
