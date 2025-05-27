
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator


@method_decorator(never_cache, name='dispatch')
class CustomSwaggerView:
    """Vista personalizada para Swagger que fuerza solo Token auth"""
    
    @staticmethod
    def get_swagger_schema():
        """Generar schema personalizado sin Basic Auth"""
        return {
            "swagger": "2.0",
            "info": {
                "title": "SuperLearner API",
                "version": "v1",
                "description": "API del Sistema SuperLearner"
            },
            "securityDefinitions": {
                "Token": {
                    "type": "apiKey",
                    "name": "Authorization",
                    "in": "header",
                    "description": "Token de autenticación. Formato: Token <tu_token_aqui>"
                }
            },
            "security": [{"Token": []}],
            "schemes": ["http", "https"],
            "host": "localhost:8000"
        }