# 📚 CRUD de Cursos - SuperLearner Peru

## 🎯 Descripción
Sistema completo de gestión de cursos (CRUD) implementado en el backend de SuperLearner Peru.

## 📋 Endpoints Disponibles

### 🔍 **1. Listar Todos los Cursos**
```http
GET /api/class/list/
Authorization: Token <tu_token>
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "name": "Matemáticas Básicas",
    "category": "Matemáticas",
    "day": "Lunes",
    "start_time": "09:00:00",
    "end_time": "11:00:00",
    "color": "#FF5733",
    "status": 1,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "duration": "2h 0m",
    "schedule_info": "Lunes de 09:00:00 a 11:00:00"
  }
]
```

### ➕ **2. Crear Nuevo Curso**
```http
POST /api/class/create/
Authorization: Token <tu_token>
Content-Type: application/json

{
  "name": "Matemáticas Básicas",
  "category": "Matemáticas",
  "day": "Lunes",
  "start_time": "09:00:00",
  "end_time": "11:00:00",
  "color": "#FF5733",
  "status": 1
}
```

**Respuesta (201 Created):**
```json
{
  "id": 1,
  "name": "Matemáticas Básicas",
  "category": "Matemáticas",
  "day": "Lunes",
  "start_time": "09:00:00",
  "end_time": "11:00:00",
  "color": "#FF5733",
  "status": 1,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "duration": "2h 0m",
  "schedule_info": "Lunes de 09:00:00 a 11:00:00"
}
```

### 🔍 **3. Obtener Curso por ID**
```http
GET /api/class/get/?course_id=1
Authorization: Token <tu_token>
```

**Respuesta:**
```json
{
  "id": 1,
  "name": "Matemáticas Básicas",
  "category": "Matemáticas",
  "day": "Lunes",
  "start_time": "09:00:00",
  "end_time": "11:00:00",
  "color": "#FF5733",
  "status": 1,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "duration": "2h 0m",
  "schedule_info": "Lunes de 09:00:00 a 11:00:00"
}
```

### ✏️ **4. Actualizar Curso**
```http
PUT /api/class/update/?course_id=1
Authorization: Token <tu_token>
Content-Type: application/json

{
  "name": "Matemáticas Avanzadas",
  "category": "Matemáticas",
  "day": "Martes",
  "start_time": "10:00:00",
  "end_time": "12:00:00",
  "color": "#00FF00",
  "status": 1
}
```

**Respuesta:**
```json
{
  "id": 1,
  "name": "Matemáticas Avanzadas",
  "category": "Matemáticas",
  "day": "Martes",
  "start_time": "10:00:00",
  "end_time": "12:00:00",
  "color": "#00FF00",
  "status": 1,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:45:00Z",
  "duration": "2h 0m",
  "schedule_info": "Martes de 10:00:00 a 12:00:00"
}
```

### 🗑️ **5. Eliminar Curso**
```http
DELETE /api/class/delete/?course_id=1
Authorization: Token <tu_token>
```

**Respuesta:**
```json
{
  "detail": "Curso 'Matemáticas Avanzadas' eliminado exitosamente."
}
```

### 🎨 **6. Actualizar Solo Color**
```http
POST /api/class/update_color/
Authorization: Token <tu_token>
Content-Type: application/json

{
  "class_id": 1,
  "color": "#FF5733"
}
```

**Respuesta:**
```json
{
  "detail": "Color updated successfully."
}
```

### 👥 **7. Obtener Cursos por Usuario y Rol**
```http
GET /api/class/get_courses/?user_id=1&role_id=1
Authorization: Token <tu_token>
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "name": "Matemáticas Básicas",
    "category": "Matemáticas",
    "day": "Lunes",
    "start_time": "09:00:00",
    "end_time": "11:00:00",
    "color": "#FF5733",
    "status": 1,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

## 📊 **Campos del Modelo Curso**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `id` | Integer | Auto | ID único del curso |
| `name` | String | ✅ | Nombre del curso |
| `category` | String | ✅ | Categoría del curso |
| `day` | String | ✅ | Día de la semana |
| `start_time` | Time | ✅ | Hora de inicio |
| `end_time` | Time | ✅ | Hora de fin |
| `color` | String | ❌ | Color del curso (hex) |
| `status` | Integer | ❌ | Estado del curso (1=activo, 0=inactivo) |
| `created_at` | DateTime | Auto | Fecha de creación |
| `updated_at` | DateTime | Auto | Fecha de última actualización |

## 🔧 **Validaciones Implementadas**

### ✅ **Validaciones Automáticas:**
1. **Hora de fin > Hora de inicio**: El `end_time` debe ser mayor que `start_time`
2. **Nombre único por día**: No puede haber dos cursos con el mismo nombre el mismo día
3. **Campos requeridos**: `name`, `category`, `day`, `start_time`, `end_time`

### ⚠️ **Códigos de Error:**
- **400**: Datos inválidos o faltantes
- **401**: No autenticado
- **403**: Sin permisos
- **404**: Curso no encontrado
- **500**: Error interno del servidor

## 🎨 **Campos Calculados**

### 📏 **Duration**
Calcula automáticamente la duración del curso:
```json
"duration": "2h 30m"
```

### 📅 **Schedule Info**
Información completa del horario:
```json
"schedule_info": "Lunes de 09:00:00 a 11:00:00"
```

## 🔐 **Autenticación y Permisos**

- **Autenticación**: Token Authentication requerida
- **Permisos**: Usuario autenticado
- **Roles**: Los coordinadores pueden ver todos los cursos, los profesores solo los suyos

## 📝 **Ejemplos de Uso**

### Crear un curso completo:
```bash
curl -X POST "http://localhost:8000/api/class/create/" \
  -H "Authorization: Token tu_token_aqui" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Inglés Básico",
    "category": "Idiomas",
    "day": "Miércoles",
    "start_time": "14:00:00",
    "end_time": "16:00:00",
    "color": "#3498db",
    "status": 1
  }'
```

### Actualizar solo el nombre:
```bash
curl -X PUT "http://localhost:8000/api/class/update/?course_id=1" \
  -H "Authorization: Token tu_token_aqui" \
  -H "Content-Type: application/json" \
  -d '{"name": "Inglés Intermedio"}'
```

## 🚀 **Características Avanzadas**

### 🔄 **Actualización Parcial**
Puedes actualizar solo los campos que necesites:
```json
{
  "name": "Nuevo Nombre"
}
```

### 🎯 **Filtrado por Usuario**
Los profesores solo ven los cursos asignados a ellos.

### 📊 **Información Enriquecida**
Cada curso incluye información calculada como duración y horario completo.

## 🛠️ **Integración con Swagger**

Todos los endpoints están documentados en Swagger:
- **URL**: `http://localhost:8000/swagger/`
- **Tag**: "📚 Cursos - CRUD"
- **Autenticación**: Usar el botón "Authorize" con tu token

## ✅ **Estado del CRUD**

| Operación | Endpoint | Método | Estado |
|-----------|----------|--------|--------|
| **Create** | `/api/class/create/` | POST | ✅ Implementado |
| **Read** | `/api/class/list/` | GET | ✅ Implementado |
| **Read One** | `/api/class/get/` | GET | ✅ Implementado |
| **Update** | `/api/class/update/` | PUT | ✅ Implementado |
| **Delete** | `/api/class/delete/` | DELETE | ✅ Implementado |

## 🎉 **¡CRUD Completo Implementado!**

El sistema de cursos ahora tiene un CRUD completo y funcional con:
- ✅ Creación de cursos
- ✅ Listado de cursos
- ✅ Obtención individual
- ✅ Actualización completa y parcial
- ✅ Eliminación de cursos
- ✅ Validaciones robustas
- ✅ Documentación completa
- ✅ Integración con Swagger


