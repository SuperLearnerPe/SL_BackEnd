# Configuración de Swagger/OpenAPI - FORZAR SOLO TOKEN
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Token': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Ingresa tu token en formato: Token <tu_token_aqui>'
        }
    },
    # DESACTIVAR COMPLETAMENTE session/basic auth
    'USE_SESSION_AUTH': False,
    'LOGIN_URL': '',
    'LOGOUT_URL': '',
    'SESSION_COOKIE_NAME': '',
    'CSRF_COOKIE_NAME': '',
    
    # Forzar que use SOLO Token auth
    'SECURITY_REQUIREMENTS': [
        {'Token': []}
    ],
    
    # Configuraciones de UI
    'JSON_EDITOR': True,
    'SUPPORTED_SUBMIT_METHODS': [
        'get', 'post', 'put', 'delete', 'patch'
    ],
    'OPERATIONS_SORTER': 'alpha',
    'TAGS_SORTER': 'alpha',
    'DOC_EXPANSION': 'none',
    'DEEP_LINKING': True,
    'SHOW_EXTENSIONS': True,
    'DEFAULT_MODEL_RENDERING': 'model',
    'VALIDATOR_URL': None,
    'CACHE_TIMEOUT': 0,
    'SPEC_URL': None,
    
    # Configuraciones para eliminar basic auth
    'PERSIST_AUTH': False,
    'REFETCH_SCHEMA_WITH_AUTH': False,
    'REFETCH_SCHEMA_ON_LOGOUT': False,
    
    # Desactivar autenticación básica
    'OAUTH2_CONFIG': {},
    'OAUTH2_REDIRECT_URL': None,
}

# Configuración de Django REST Framework - SOLO Token Authentication
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        # IMPORTANTE: NO incluir SessionAuthentication para evitar Basic auth en Swagger
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    # Desactivar completamente la autenticación de sesión para Swagger
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
}