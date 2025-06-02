# SuperLearner Peru - Backend API 🎓

## 📋 Descripción del Proyecto

SuperLearner Peru es un **sistema integral de gestión estudiantil** desarrollado con Django REST Framework que permite administrar estudiantes, voluntarios, padres de familia, control de asistencias y generar reportes detallados con métricas de impacto educativo.

### 🎯 Objetivos
- Centralizar la gestión de estudiantes y voluntarios
- Automatizar el control de asistencias
- Generar métricas de impacto educativo
- Proporcionar reportes ejecutivos en Excel
- Facilitar la toma de decisiones basada en datos

## ✨ Características Principales

- 🎓 **Gestión de Estudiantes**: CRUD completo con información personal y académica
- 👥 **Gestión de Voluntarios**: Administración de personal y coordinadores  
- 👨‍👩‍👧‍👦 **Gestión de Padres**: Vinculación familiar con estudiantes
- 📊 **Control de Asistencias**: Sistema detallado por sesión y clase
- 📈 **Métricas Avanzadas**: Reportes Excel con análisis de impacto y gestión
- 🔐 **Autenticación Segura**: Sistema de tokens JWT
- 📚 **API Documentada**: Swagger/OpenAPI integrado
- 🚀 **Optimizado**: Consultas de BD optimizadas para alto rendimiento
- 🌐 **CORS Configurado**: Listo para frontend desplegado
- 📱 **Responsive**: API preparada para apps móviles

## 🛠️ Stack Tecnológico

### Backend
- **Framework**: Django 5.1 + Django REST Framework 3.15.2
- **Lenguaje**: Python 3.12+
- **Base de Datos**: PostgreSQL (prod) / MySQL (dev)
- **Autenticación**: Django Token Authentication
- **Documentación**: drf-yasg (Swagger UI)
- **Servidor**: Gunicorn + WhiteNoise

### Reportes y Análisis
- **Procesamiento**: pandas 2.2.3
- **Excel**: openpyxl 3.1.5 + xlsxwriter 3.2.3
- **Optimización**: Django ORM con select_related/prefetch_related

### Deployment y DevOps
- **Cloud**: Google Cloud Run
- **Contenedores**: Docker + Docker Compose
- **CORS**: django-cors-headers
- **Variables**: python-dotenv + django-environ
- **Logs**: Configuración estructurada


## 🚀 Inicio Rápido

### Prerrequisitos
- Python 3.12+
- PostgreSQL 12+ (recomendado) o MySQL 8+
- Git
- Docker (opcional)

### ⚡ Instalación en 5 minutos

1. **Clonar y configurar entorno**
   ```bash
   git clone <repository-url>
   cd SL_BackEnd
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   # Linux/Mac  
   source .venv/bin/activate
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

4. **Configurar base de datos**
   ```bash
   # PostgreSQL (recomendado)
   createdb superlearner_db
   
   # En .env
   DATABASE_URL=postgresql://usuario:password@localhost:5432/superlearner_db
   ```

5. **Ejecutar migraciones y crear superusuario**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **¡Ejecutar servidor!**
   ```bash
   python manage.py runserver
   ```

   🎉 **¡Listo!** Visita:
   - API: http://localhost:8000/api/
   - Swagger: http://localhost:8000/swagger/
   - Admin: http://localhost:8000/admin/

### 🐳 Con Docker (Alternativa)

```bash
# Desarrollo
docker-compose up dev

# Producción local
docker build -t superlearner-backend .
docker run -p 8000:8000 superlearner-backend
```

## 📚 Documentación de API

### 🔐 Autenticación
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "tu_usuario",
  "password": "tu_password"
}

# Respuesta
{
  "token": "abc123...",
  "user": {
    "id": 1,
    "username": "tu_usuario"
  }
}
```

### 👨‍🎓 Estudiantes
```http
# Listar estudiantes
GET /api/students/
Authorization: Token abc123...

# Crear estudiante
POST /api/students/
Authorization: Token abc123...
Content-Type: application/json

{
  "name": "Juan",
  "last_name": "Pérez",
  "email": "juan@email.com",
  "phone": "123456789",
  "gender": "M",
  "birthdate": "2000-01-15"
}
```


### 📖 Documentación Interactiva
- **Swagger UI**: `/swagger/` - Documentación interactiva completa

## 📊 Sistema de Métricas

### 🎯 Métricas de Impacto
- **Tasa de Asistencia**: General y por clase/período
- **Alumnos Regulares**: ≥50% de asistencia
- **Frecuencia de Asistencia**: Categorización 1-3, 4-5, 6+ veces
- **Retención**: Análisis mes a mes
- **Tendencias**: Días con mayor/menor asistencia
- **Promedios**: Sesiones por alumno por período

### 📋 Métricas de Gestión
- **Listas de Asistencia**: Diaria/semanal/mensual
- **Alumnos en Riesgo**: <25% de asistencia
- **Análisis Demográfico**: Grupos por edad/género
- **Faltas Consecutivas**: >30 faltas seguidas
- **Resumen por Clases**: Estadísticas detalladas

### 📈 Reportes Excel Optimizados
- **Consultas Optimizadas**: Sin consultas N+1
- **Grandes Volúmenes**: Manejo eficiente de datos
- **Múltiples Hojas**: Organización por tipo de métrica
- **Gráficos**: Visualizaciones automáticas
- **Filtros**: Fecha, clase, estudiante específico

## 🔧 Configuración Avanzada

### 🌍 Variables de Entorno

```env
# Configuración General
SECRET_KEY=tu-clave-secreta-muy-segura
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# Base de Datos
DATABASE_URL=postgresql://user:pass@host:port/db

# Email
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password

# CORS (Producción)
CORS_ALLOWED_ORIGINS=https://tu-frontend.com
```

### 🚀 Deployment en Google Cloud Run

```bash
# 1. Construir imagen
docker build -t gcr.io/[PROJECT-ID]/superlearner-backend .

# 2. Subir a Container Registry
docker push gcr.io/[PROJECT-ID]/superlearner-backend


### 🔒 Configuración CORS
El proyecto está preconfigurado para:
- **Frontend**: `https://front-as-sl-1083661745884.southamerica-west1.run.app`
- **Backend**: `https://backend-superlearner-1083661745884.us-central1.run.app`
- **Swagger**: Funciona desde cualquier origen en producción


## 👥 Contribuir al Proyecto

### 🔄 Flujo de Trabajo
1. **Fork** del repositorio
2. **Crear rama**: `git checkout -b feature/nueva-funcionalidad`
3. **Desarrollar** con tests
4. **Commit**: `git commit -m 'feat: agregar nueva funcionalidad'`
5. **Push**: `git push origin feature/nueva-funcionalidad`
6. **Pull Request** con descripción detallada

### 📋 Estándares
- ✅ Seguir **PEP 8**
- ✅ **Documentar** funciones complejas
- ✅ **Tests** para nuevas funcionalidades
- ✅ **Commit messages** descriptivos
- ✅ **Code review** obligatorio


### 🌟 ¡Gracias por usar SuperLearner Peru!

**Construido con ❤️ para impactar la educación en Peru**

## Características Principales

- 🎓 **Gestión de Estudiantes**: CRUD completo de estudiantes con información personal y académica
- 👥 **Gestión de Voluntarios**: Administración de personal voluntario y coordinadores
- 👨‍👩‍👧‍👦 **Gestión de Padres**: Vinculación de padres de familia con estudiantes
- 📊 **Sistema de Asistencias**: Control detallado de asistencias por sesión y clase
- 📈 **Métricas Avanzadas**: Generación de reportes Excel con métricas de impacto y gestión
- 🔐 **Autenticación por Token**: Sistema seguro de autenticación
- 📚 **Documentación API**: Swagger/OpenAPI integrado

## Tecnologías Utilizadas

- **Backend**: Django 5.1 + Django REST Framework 3.15.2
- **Base de Datos**: PostgreSQL (producción) / MySQL (desarrollo)
- **Autenticación**: Django Token Authentication
- **Documentación**: drf-yasg (Swagger)
- **Reportes**: pandas + openpyxl + xlsxwriter
- **Deployment**: Google Cloud Run
- **CORS**: django-cors-headers
- **Servidor**: Gunicorn

## Configuración del Entorno de Desarrollo

### Prerrequisitos

- Python 3.12+
- PostgreSQL o MySQL
- Git
- Docker (opcional)

## API Endpoints

### Autenticación
- `POST /api/auth/login/` - Iniciar sesión
- `POST /api/auth/logout/` - Cerrar sesión
- `POST /api/auth/register/` - Registrar usuario

### Estudiantes
- `GET /api/students/` - Listar estudiantes
- `POST /api/students/` - Crear estudiante
- `GET /api/students/{id}/` - Obtener estudiante
- `PUT /api/students/{id}/` - Actualizar estudiante
- `DELETE /api/students/{id}/` - Eliminar estudiante

### Voluntarios
- `GET /api/volunteers/` - Listar voluntarios
- `POST /api/volunteers/` - Crear voluntario
- `GET /api/volunteers/{id}/` - Obtener voluntario
- `PUT /api/volunteers/{id}/` - Actualizar voluntario

### Asistencias
- `GET /api/attendance/` - Listar asistencias
- `POST /api/attendance/` - Registrar asistencia
- `GET /api/attendance/session/{session_id}/` - Asistencias por sesión

### Métricas
- `GET /metricas/impacto/` - Métricas de impacto
- `GET /metricas/impacto/excel/` - Reporte Excel de impacto
- `GET /metricas/gestion/` - Métricas de gestión
- `GET /metricas/gestion/excel/` - Reporte Excel de gestión

### Documentación
- `/swagger/` - Documentación interactiva Swagger
- `/redoc/` - Documentación ReDoc


### Configuración CORS
El proyecto está configurado para los siguientes dominios:
- Frontend: `https://front-as-sl-1083661745884.southamerica-west1.run.app`
- Backend: `https://backend-superlearner-1083661745884.us-central1.run.app`

