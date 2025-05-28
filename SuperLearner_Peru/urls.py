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

# Importar ViewSets del módulo métricas
from metricas.views import ImpactoViewSet, GestionViewSet

# Configuración del esquema de API simplificada
schema_view = get_schema_view(
    openapi.Info(
        title="SuperLearner Peru API",
        default_version='v1',
        description="""
## API del Sistema SuperLearner Peru

Esta API proporciona acceso completo al sistema de gestión educativa SuperLearner Peru.

### 🔐 Autenticación
**IMPORTANTE**: Todos los endpoints requieren autenticación mediante token.

**Pasos para autenticarse:**
1. Obtén tu token usando el endpoint `/api/user/login/`
2. Haz clic en el botón "🔒 Authorize" arriba
3. En el campo "Value" escribe: `Token <tu_token_aqui>`
4. Haz clic en "Authorize"
5. ¡Listo! Ahora puedes usar todos los endpoints

### 📋 Endpoints Principales
- **🔐 Autenticación**: Login y registro de usuarios
- **👤 Usuario**: Información de perfil de usuario
- **📚 Cursos**: Gestión de clases y cursos
- **👥 Estudiantes**: Gestión de estudiantes y asistencia
- **🛠️ Soporte**: Sistema de soporte técnico
- **📊 Métricas**: Generación de reportes Excel
        """,
        contact=openapi.Contact(name="Soporte SuperLearner Peru", email="soporte@superlearner.pe"),
        license=openapi.License(name="Privado"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[],
)

# Configuración del router principal
router = DefaultRouter()
router.register(r'user', UserViewSet, basename='user')
router.register(r'class', ClassViewSset, basename='class')  
router.register(r'student', StudentsViewset, basename='student')
router.register(r'support', SupportViewset, basename='support')

# Registrar ViewSets del módulo métricas
router.register(r'metricas/impacto', ImpactoViewSet, basename='metricas-impacto')
router.register(r'metricas/gestion', GestionViewSet, basename='metricas-gestion')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include(router.urls)),
    
    # Documentación Swagger únicamente
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    
    # Endpoint principal redirige a Swagger
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),
]
