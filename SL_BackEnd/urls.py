from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import UserViewSet, ClassViewSset, StudentsViewset, SupportViewset
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from drf_yasg.generators import OpenAPISchemaGenerator
from django.conf import settings

class CustomOpenAPISchemaGenerator(OpenAPISchemaGenerator):
    def get_security_definitions(self):
        """Definir ÚNICAMENTE Token authentication"""
        return {
            'Token': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header',
                'description': 'Ingresa tu token en formato: Token <tu_token_aqui>'
            }
        }
    
    def get_security_requirements(self, path, method, view):
        """Aplicar Token security SOLO a endpoints que requieren autenticación"""
        # Solo endpoints que no sean login o register requieren token
        if '/login/' in path or '/register/' in path:
            return []
        return [{'Token': []}]
    
    def get_schema(self, request=None, public=False):
        """Sobrescribir para eliminar cualquier autenticación básica"""
        schema = super().get_schema(request, public)
        
        # Asegurar que solo existe Token auth
        if 'securityDefinitions' in schema:
            schema['securityDefinitions'] = {
                'Token': {
                    'type': 'apiKey',
                    'name': 'Authorization',
                    'in': 'header',
                    'description': 'Ingresa tu token en formato: Token <tu_token_aqui>'
                }
            }
        
        return schema

# Configuración del esquema de API con Token únicamente - SIN CACHE
schema_view = get_schema_view(
    openapi.Info(
        title="SuperLearner API",
        default_version='v1',
        description="""
## API del Sistema SuperLearner

Esta API proporciona acceso completo al sistema de gestión educativa SuperLearner.

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
        """,
        contact=openapi.Contact(name="Soporte SuperLearner", email="soporte@superlearner.com"),
        license=openapi.License(name="Privado"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[],
    generator_class=CustomOpenAPISchemaGenerator,
    # Configuración específica para eliminar basic auth
    url='http://localhost:8000/',  # Forzar URL específica
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
    
    # Solo Documentación Swagger (FORZANDO sin cache y sin Basic Auth)
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    
    # Endpoint principal redirige a Swagger
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),
]

# Configuraciones adicionales para el contexto del template

if hasattr(settings, 'SWAGGER_SETTINGS'):
    settings.SWAGGER_SETTINGS['SECURITY_REQUIREMENTS'] = [{'Token': []}]