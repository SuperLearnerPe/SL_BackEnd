from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from .serializers import UserDataSerializer,UserSerializer, GetCourses ,CourseSerializer  
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
# from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import  Class ,Volunteers ,VolunteerClass 
from django.core.mail import send_mail
from django.db import transaction

# Esquemas reutilizables para Swagger
def get_auth_header():
    """
    DEPRECATED: Ya no se usa en los endpoints individuales.
    La autenticación ahora es global usando el botón 'Authorize' en Swagger.
    """
    return openapi.Parameter(
        'Authorization',
        openapi.IN_HEADER,
        description="Token de autenticación en formato: 'Token <token_value>'",
        type=openapi.TYPE_STRING,
        required=False  # Cambiado a False porque ahora es global
    )

# Respuestas comunes para Swagger
COMMON_RESPONSES = {
    400: openapi.Response(
        description="Solicitud incorrecta",
        examples={
            "application/json": {
                "error": "Datos de entrada inválidos"
            }
        }
    ),
    401: openapi.Response(
        description="No autorizado",
        examples={
            "application/json": {
                "detail": "Las credenciales de autenticación no se proporcionaron."
            }
        }
    ),
    403: openapi.Response(
        description="Acceso prohibido",
        examples={
            "application/json": {
                "error": "No tienes permisos para realizar esta acción"
            }
        }
    ),
    404: openapi.Response(
        description="No encontrado",
        examples={
            "application/json": {
                "detail": "Recurso no encontrado"
            }
        }
    ),
    500: openapi.Response(
        description="Error interno del servidor",
        examples={
            "application/json": {
                "detail": "Error interno del servidor"
            }
        }
    )
}

class UserViewSet(ViewSet):
    
    authentication_classes = [TokenAuthentication]
    permission_classes = []  # Se configura por método individual
    
    @swagger_auto_schema(
        operation_summary="Login de usuario",
        operation_description="Autenticar usuario con email y password. Devuelve token de autenticación.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Email del usuario',
                    example='usuario@ejemplo.com'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Contraseña del usuario',
                    example='miPassword123'
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description='Login exitoso',
                examples={
                    "application/json": {
                        "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
                        "user": {
                            "id": 1,
                            "email": "usuario@ejemplo.com",
                            "all_permissions": [],
                            "groups": [],
                            "role": 1
                        }
                    }
                }
            ),
            400: openapi.Response(
                description='Datos incorrectos',
                examples={
                    "application/json": {
                        "error": "Email is required"
                    }
                }
            ),
            403: openapi.Response(
                description='Cuenta inactiva',
                examples={
                    "application/json": {
                        "error": "This account is inactive."
                    }
                }
            ),
            404: openapi.Response(
                description='Usuario no encontrado',
                examples={
                    "application/json": {
                        "error": "User not found"
                    }
                }
            )
        },
        tags=["🔐 Autenticación"]
    )
    @action(detail=False, methods=['POST'], permission_classes=[])
    def login(self, request):
        try:
            email = request.data.get("email", "").lower().strip()
            password = request.data.get("password")

            # Verify that both fields are present
            if not email:
                return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            if not password:
                return Response({"error": "Password is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Try to get the user by email
            user = get_object_or_404(User, email=email)

            # Verify the password
            if not user.check_password(password):
                return Response({"error": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the user is active in the Volunteers table
            volunteer = get_object_or_404(Volunteers, user_id=user.id)
            if volunteer.status != 1:
                return Response({"error": "This account is inactive."}, status=status.HTTP_403_FORBIDDEN)

            # Generate or retrieve the token
            Token.objects.filter(user=user).delete()  # Optionally delete old tokens
            token, created = Token.objects.get_or_create(user=user)

            # Serialize the user
            serializer = UserSerializer(instance=user)

            # Respond with the token and user data
            return Response({
                "token": token.key,
                "user": serializer.data
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print(f"Unexpected error: {str(e)}")  # For debugging
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        operation_summary="Registro de usuario",
        operation_description="Crear una nueva cuenta de usuario",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Email del usuario',
                    example='nuevo@ejemplo.com'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Contraseña del usuario',
                    example='password123'
                ),
            },
        ),
        responses={
            201: openapi.Response(
                description='Usuario creado exitosamente',
                examples={
                    "application/json": {
                        "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
                        "user": {
                            "id": 2,
                            "email": "nuevo@ejemplo.com",
                            "all_permissions": [],
                            "groups": [],
                            "role": None
                        }
                    }
                }
            ),
            400: COMMON_RESPONSES[400],
            500: COMMON_RESPONSES[500]
        },
        tags=["🔐 Autenticación"]
    )
    @action(detail=False, methods=['POST'], permission_classes=[])
    def register(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    serializer.save()
                    user = User.objects.get(email=serializer.data["email"])
                    user.set_password(serializer.data["password"])
                    user.save()
                    token = Token.objects.create(user=user)
                return Response({"token": token.key, "user": serializer.data}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Perfil del usuario",
        operation_description="Obtener información del perfil del usuario autenticado",
        security=[{'Token': []}],
        responses={
            200: openapi.Response(
                description='Perfil obtenido exitosamente',
                schema=UserSerializer,
                examples={
                    "application/json": {
                        "id": 1,
                        "email": "usuario@ejemplo.com",
                        "all_permissions": [],
                        "groups": [],
                        "role": 1
                    }
                }
            ),
            401: COMMON_RESPONSES[401],
            403: COMMON_RESPONSES[403]
        },
        tags=["👤 Usuario"]
    )
    @action(detail=False, methods=['GET'])
    def profile(self, request):
        serializer = UserSerializer(instance=request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_summary="Datos del usuario",
        operation_description="Obtener información detallada del usuario (voluntario)",
        security=[{'Token': []}],
        manual_parameters=[
            openapi.Parameter(
                'id_user',
                openapi.IN_QUERY,
                description="ID del usuario a consultar",
                type=openapi.TYPE_INTEGER,
                required=True,
                example=1
            )
        ],
        responses={
            200: openapi.Response(
                description='Datos del usuario obtenidos exitosamente',
                schema=UserDataSerializer(many=True),
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "name": "Juan",
                            "last_name": "Pérez",
                            "personal_email": "juan@gmail.com",
                            "photo": None,
                            "phone": "+51987654321",
                            "user_id": 1,
                            "email": "juan@superlearner.com"
                        }
                    ]
                }
            ),
            400: COMMON_RESPONSES[400],
            404: COMMON_RESPONSES[404],
            500: COMMON_RESPONSES[500]
        },
        tags=["👤 Usuario"]
    )
    @action(detail=False, methods=['GET'])
    def Data_user(self, request):
        id_user = request.query_params.get('id_user')  # Utiliza query_params para GET requests
        
        if not id_user:
            return Response({"detail": "El parámetro 'id_user' es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data_user = Volunteers.objects.filter(user_id=id_user)
            
            if data_user.exists():
                serializer = UserDataSerializer(data_user, many=True)  # Usa UserDataSerializer aquí
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "No se encontraron voluntarios para el ID proporcionado."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                   
class ClassViewSset(ViewSet):
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Obtener cursos",
        operation_description="Obtener lista de cursos. Si el usuario es coordinador, retorna todos los cursos. Si es profesor, retorna solo los cursos asignados.",
        security=[{'Token': []}],
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_QUERY,
                description="ID del usuario",
                type=openapi.TYPE_INTEGER,
                required=True,
                example=1
            ),
            openapi.Parameter(
                'role_id',
                openapi.IN_QUERY,
                description="ID del rol del usuario (1=Coordinador, 2=Profesor)",
                type=openapi.TYPE_STRING,
                required=True,
                example="2"
            )
        ],
        responses={
            200: openapi.Response(
                description='Lista de cursos obtenida exitosamente',
                schema=GetCourses(many=True),
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "category": "Inglés",
                            "name": "Inglés Básico",
                            "day": "Lunes",
                            "start_time": "09:00:00",
                            "end_time": "11:00:00",
                            "color": "#FF5733",
                            "status": 1,
                            "created_at": "2024-01-01T10:00:00Z",
                            "updated_at": "2024-01-01T10:00:00Z"
                        }
                    ]
                }
            ),
            400: COMMON_RESPONSES[400],
            500: COMMON_RESPONSES[500]
        },
        tags=["📚 Cursos"]
    )
    @action(detail=False, methods=['GET'], url_path='get_courses', permission_classes=[IsAuthenticated])
    def get_schedules(self, request):
        # Obtener el ID del usuario desde los parámetros de consulta
        user_id = request.query_params.get('user_id')
        role_id = request.query_params.get('role_id')
    
        if user_id is None or role_id is None:
            return Response({"detail": "user_id and role_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verificar si el usuario tiene el rol de coordinador (suponiendo que 1 es el ID del coordinador)
            is_coordinator = (role_id == "1")

            if is_coordinator:
                # Si el usuario es coordinador, retornar todos los cursos
                courses = Class.objects.all()
            else:
                # Si el usuario no es coordinador, retornar solo los cursos asociados
                # Obtener el ID del voluntario asociado al usuario
                volunteer = Volunteers.objects.get(user_id=user_id)

                # Filtrar cursos basados en el ID del voluntario
                courses = Class.objects.filter(
                    volunteerclass__id_volunteer=volunteer.id
                ).distinct()  # Asegúrate de no obtener duplicados

        except Volunteers.DoesNotExist:
            # Si el usuario no es un voluntario, no devolver cursos
            courses = Class.objects.none()
            print("No volunteer found for this user.")
        except Exception as e:
            # Manejar cualquier otra excepción
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        course_serializer = GetCourses(courses, many=True)
        return Response(course_serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Obtener curso por ID",
        operation_description="Obtener información detallada de un curso específico por su ID",
        security=[{'Token': []}],
        manual_parameters=[
            openapi.Parameter(
                'course_id',
                openapi.IN_QUERY,
                description="ID del curso a consultar",
                type=openapi.TYPE_INTEGER,
                required=True,
                example=1
            )
        ],
        responses={
            200: openapi.Response(
                description='Curso obtenido exitosamente',
                schema=CourseSerializer,
                examples={
                    "application/json": {
                        "id": 1,
                        "category": "Inglés",
                        "name": "Inglés Básico",
                        "day": "Lunes",
                        "start_time": "09:00:00",
                        "end_time": "11:00:00",
                        "color": "#FF5733",
                        "status": 1,
                        "created_at": "2024-01-01T10:00:00Z",
                        "updated_at": "2024-01-01T10:00:00Z"
                    }
                }
            ),
            400: COMMON_RESPONSES[400],
            404: COMMON_RESPONSES[404],
            500: COMMON_RESPONSES[500]
        },
        tags=["📚 Cursos"]
    )
    @action(detail=False, methods=['GET'], url_path='get_Courses_id')
    def get_schedules_id(self, request):
        course_id = request.query_params.get('course_id', None)
        if not course_id:
            return Response({"detail": "El ID del curso es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        course = get_object_or_404(Class.objects, id=course_id)
        serializer = CourseSerializer(course)
        return Response(serializer.data, status=status.HTTP_200_OK) 
    
    
    @swagger_auto_schema(
        operation_summary="Actualizar color del curso",
        operation_description="Actualizar el color de un curso específico",
        security=[{'Token': []}],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['class_id', 'color'],
            properties={
                'class_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID del curso',
                    example=1
                ),
                'color': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Nuevo color en formato hexadecimal',
                    example='#FF5733'
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description='Color actualizado exitosamente',
                examples={
                    "application/json": {
                        "detail": "Color updated successfully."
                    }
                }
            ),
            400: COMMON_RESPONSES[400],
            404: COMMON_RESPONSES[404],
            500: COMMON_RESPONSES[500]
        },
        tags=["📚 Cursos"]
    )
    @action(detail=False, methods=['POST'], url_path='update_color')
    def update_color(self, request):
        class_id = request.data.get('class_id')
        color = request.data.get('color')
        
        if not class_id or not color:
            return Response({"detail": "class_id and color are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Obtener la clase por ID
            class_obj = Class.objects.get(id=class_id)
            
            # Actualizar el color de la clase
            class_obj.color = color
            class_obj.save()

            return Response({"detail": "Color updated successfully."}, status=status.HTTP_200_OK)
        
        except Class.DoesNotExist:
            return Response({"detail": "Class not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
# class StudentsViewset(ViewSet): 
    
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]

#     @swagger_auto_schema(
#         operation_summary="Obtener todos los estudiantes",
#         operation_description="Obtener lista completa de estudiantes registrados",
#         security=[{'Token': []}],
#         responses={
#             200: openapi.Response(
#                 description='Lista de estudiantes obtenida exitosamente',
#                 schema=GetStudentsClass(many=True)
#             ),
#             401: COMMON_RESPONSES[401],
#             403: COMMON_RESPONSES[403]
#         },
#         tags=["👥 Estudiantes"]
#     )
#     @action(detail=False, methods=['GET'], url_path='getStudents')
#     def get_students(self, request):
#         course = Students.objects.all()
#         serializer = GetStudentsClass(course,many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)

#     @swagger_auto_schema(
#         operation_summary="Obtener estudiantes por clase",
#         operation_description="Obtener lista de estudiantes filtrados por ID de clase",
#         security=[{'Token': []}],
#         manual_parameters=[
#             openapi.Parameter(
#                 'class_id',
#                 openapi.IN_QUERY,
#                 description="ID de la clase para filtrar estudiantes",
#                 type=openapi.TYPE_INTEGER,
#                 required=True,
#                 example=1
#             )
#         ],
#         responses={
#             200: openapi.Response(
#                 description='Estudiantes de la clase obtenidos exitosamente',
#                 schema=GetStudentsClass(many=True)
#             ),
#             400: COMMON_RESPONSES[400],
#             404: COMMON_RESPONSES[404],
#             500: COMMON_RESPONSES[500]
#         },
#         tags=["👥 Estudiantes"]
#     )
#     @action(detail=False, methods=['GET'], url_path='getStudents_id')
#     def get_students_id(self, request):
#         try:
#             class_id = request.query_params.get('class_id', None)

#             if not class_id:
#                 return Response({"detail": "El ID de la clase es requerido."}, status=status.HTTP_400_BAD_REQUEST)

#             # Obtenemos los estudiantes que pertenecen a una clase específica
#             resultados = Students.objects.filter(
#                 studentclass__id_class=class_id
#             )

#             if not resultados.exists():
#                 return Response({"detail": "Estudiantes no encontrados."}, status=status.HTTP_404_NOT_FOUND)

#             # Serializar los resultados
#             serializer = GetStudentsClass(resultados, many=True)
#             return Response(serializer.data, status=status.HTTP_200_OK)
        
#         except Exception as e:
#             return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     @swagger_auto_schema(
#         operation_summary="Actualizar estado de asistencia",
#         operation_description="Actualizar el estado de asistencia para múltiples estudiantes en una sesión específica",
#         security=[{'Token': []}],
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             required=['attendances', 'num_session', 'id_class'],
#             properties={
#                 'attendances': openapi.Schema(
#                     type=openapi.TYPE_ARRAY,
#                     description="Lista de asistencias a actualizar",
#                     items=openapi.Schema(
#                         type=openapi.TYPE_OBJECT,
#                         required=['id', 'attendance'],
#                         properties={
#                             'id': openapi.Schema(
#                                 type=openapi.TYPE_INTEGER,
#                                 description="ID del estudiante",
#                                 example=127
#                             ),
#                             'attendance': openapi.Schema(
#                                 type=openapi.TYPE_STRING,
#                                 enum=['PRESENT', 'TARDY', 'ABSENT', 'JUSTIFIED', ''],
#                                 description="Estado de asistencia (PRESENT=Presente, TARDY=Tardanza, ABSENT=Falta, JUSTIFIED=Justificado, ''=No registrado)",
#                                 example="PRESENT"
#                             ),
#                         },
#                     )
#                 ),
#                 'num_session': openapi.Schema(
#                     type=openapi.TYPE_INTEGER,
#                     description="Número de sesión",
#                     example=1
#                 ),
#                 'id_class': openapi.Schema(
#                     type=openapi.TYPE_INTEGER,
#                     description="ID de la clase",
#                     example=1
#                 )
#             },
#         ),
#         responses={
#             200: openapi.Response(
#                 description='Estados de asistencia actualizados exitosamente',
#                 examples={
#                     "application/json": {
#                         "message": "Attendance statuses updated successfully.",
#                     }
#                 }
#             ),
#             400: openapi.Response(
#                 description='Datos de entrada inválidos',
#                 examples={
#                     "application/json": {
#                         "error": "Valor de asistencia no válido. Valores permitidos: PRESENT, TARDY, ABSENT, JUSTIFIED, "
#                     }
#                 }
#             ),
#             401: COMMON_RESPONSES[401],
#             403: COMMON_RESPONSES[403]
#         },
#         tags=["👥 Estudiantes"]
#     )
#     @action(detail=False, methods=['PUT'], url_path='update_statuses_students')
#     def update_attendance_statuses(self, request):
#         attendances_data = request.data.get('attendances', [])

#         if not isinstance(attendances_data, list):
#             return Response({'error': 'Invalid data format. Expected a list of attendances.'}, status=status.HTTP_400_BAD_REQUEST)

#         # Validar los valores de asistencia
#         valid_attendance_values = ['PRESENT', 'TARDY', 'ABSENT', 'JUSTIFIED', '']
#         for item in attendances_data:
#             if 'attendance' not in item or item['attendance'] not in valid_attendance_values:
#                 return Response(
#                     {'error': f'Valor de asistencia no válido. Valores permitidos: {", ".join(valid_attendance_values)}'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         session_number = request.data.get('num_session')
#         class_id = request.data.get('id_class')

#         if not session_number or not class_id:
#             return Response({'error': 'Session number and class ID are required.'}, status=status.HTTP_400_BAD_REQUEST)

#         updated_attendances = []

#         for item in attendances_data:
#             # Filtrar por el número de sesión (num_session) y la clase (id_class)
#             attendances = AttendanceStudent.objects.filter(
#                 id_student=item['id'],
#                 id_session__num_session=session_number,  # Usar la relación con la tabla Session
#                 id_session__id_class=class_id  # Asegurarse de que la sesión pertenece a la clase correcta
#             )
            
#             if attendances.exists():
#                 for attendance in attendances:
#                     attendance.attendance = item['attendance']
#                     updated_attendances.append(attendance)

#         if updated_attendances:
#             # Actualizar los registros modificados
#             AttendanceStudent.objects.bulk_update(updated_attendances, ['attendance'])

#         return Response({
#             'message': 'Attendance statuses updated successfully.',
#             'attendance_legend': {
#                 'PRESENT': 'Presente',
#                 'TARDY': 'Tardanza',
#                 'ABSENT': 'Falta',
#                 'JUSTIFIED': 'Justificado',
#                 '': 'No registrado'
#             }
#         }, status=status.HTTP_200_OK)
    
#     @swagger_auto_schema(
#         operation_summary="Crear nueva sesión",
#         operation_description="Crear una nueva sesión para una clase. Los estudiantes se registran automáticamente con asistencia en blanco.",
#         security=[{'Token': []}],
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             required=['id_class'],
#             properties={
#                 'id_class': openapi.Schema(
#                     type=openapi.TYPE_INTEGER,
#                     description='ID de la clase',
#                     example=1
#                 )
#             },
#         ),
#         responses={
#             201: openapi.Response(
#                 description='Sesión creada exitosamente',
#                 examples={
#                     "application/json": {
#                         "message": "Sesión creada con éxito y asistencia registrada en blanco",
#                         "session": {
#                             "id_session": 4,
#                             "id_class": 1,
#                             "num_session": 2,
#                             "date": "2025-05-08T04:15:30Z"
#                         },
#                         "student_count": 15
#                     }
#                 }
#             ),
#             400: openapi.Response(
#                 description='Error en la solicitud',
#                 examples={
#                     "application/json": {
#                         "error": "No hay estudiantes asociados a esta clase. No se puede crear una sesión.",
#                         "status": "EMPTY_CLASS"
#                     }
#                 }
#             ),
#             401: COMMON_RESPONSES[401],
#             403: COMMON_RESPONSES[403],
#             404: COMMON_RESPONSES[404]
#         },
#         tags=["👥 Estudiantes"]
#     )
#     @action(detail=False, methods=['POST'], url_path='create_session')
#     def create_session(self, request, *args, **kwargs):
#         try:
#             logged_in_user = request.user

#             # Consultar los roles del usuario
#             user_roles = AuthUserRoles.objects.filter(user=logged_in_user).select_related('role')

#             # Verificar si el usuario tiene el rol de admin o profesor
#             is_volunteer = user_roles.filter(role__name='Volunteers_Profesor').exists()
#             is_admin = user_roles.filter(role__name='admin').exists()

#             if not (is_volunteer or is_admin):
#                 return Response({'error': 'No tienes permisos para realizar esta acción'}, status=status.HTTP_403_FORBIDDEN)

#             # Obtener la clase por su ID
#             class_id = request.data.get('id_class')
#             if not class_id:
#                 return Response({'error': 'ID de la clase no proporcionado'}, status=status.HTTP_400_BAD_REQUEST)

#             try:
#                 course_class = Class.objects.get(id=class_id)
#             except Class.DoesNotExist:
#                 return Response({'error': 'Clase no encontrada'}, status=status.HTTP_404_NOT_FOUND)

#             # Verificar si hay estudiantes asociados a esta clase ANTES de crear la sesión
#             student_count = Students.objects.filter(studentclass__id_class=course_class.id).count()
#             if student_count == 0:
#                 return Response({
#                     'error': 'No hay estudiantes asociados a esta clase. No se puede crear una sesión.',
#                     'status': 'EMPTY_CLASS'
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             volunteer = None  # Inicializar voluntario como None

#             if is_volunteer:
#                 # Verificar si el usuario es un voluntario asociado a esta clase
#                 try:
#                     volunteer = Volunteers.objects.get(user=logged_in_user)
#                 except Volunteers.DoesNotExist:
#                     return Response({'error': 'El usuario no es un profesor'}, status=status.HTTP_403_FORBIDDEN)

#                 if not VolunteerClass.objects.filter(id_class=course_class.id, id_volunteer=volunteer.id).exists():
#                     return Response({'error': 'No tienes permiso para crear sesiones en esta clase.'}, status=status.HTTP_403_FORBIDDEN)

#             elif is_admin:
#                 # Si el usuario es admin, buscar el primer voluntario asociado al curso
#                 volunteer_class = VolunteerClass.objects.filter(id_class=course_class.id).select_related('id_volunteer').first()
#                 if not volunteer_class:
#                     return Response({'error': 'No se encontraron voluntarios asociados a esta clase'}, status=status.HTTP_404_NOT_FOUND)
#                 volunteer = volunteer_class.id_volunteer

#             # Obtener el último número de sesión para la clase
#             last_session = Session.objects.filter(id_class=course_class).order_by('-num_session').first()
#             num_session = (last_session.num_session + 1) if last_session else 1

#             # Usar transacción para garantizar atomicidad
#             with transaction.atomic():
#                 # Crear una nueva sesión
#                 session = Session.objects.create(
#                     id_class=course_class,
#                     num_session=num_session,
#                     date=timezone.now(),
#                 )

#                 # Obtener estudiantes asociados a la clase
#                 students = Students.objects.filter(studentclass__id_class=course_class.id)
                
#                 # Crear registros de asistencia para cada estudiante (con asistencia en blanco)
#                 attendance_records = []
#                 failed_students = []
                
#                 for student in students:
#                     try:
#                         attendance_records.append(
#                             AttendanceStudent(
#                                 id_student=student,
#                                 id_volunteer=volunteer,
#                                 id_session=session,
#                                 created_date=timezone.now(),
#                                 attendance=""  
#                             )
#                         )
#                     except Exception as e:
#                         failed_students.append({"id": student.id, "error": str(e)})
                
#                 # Guardar todas las asistencias en batch para mejor rendimiento
#                 if attendance_records:
#                     AttendanceStudent.objects.bulk_create(attendance_records)

#                 # Serializar la sesión creada
#                 serializer = SessionSerializer(session)
                
#                 response_data = {
#                     'message': 'Sesión creada con éxito y asistencia registrada en blanco',
#                     'session': serializer.data,
#                     'student_count': student_count

#                 }
                
#                 # Incluir información sobre errores si los hay
#                 if failed_students:
#                     response_data['warning'] = 'Algunos estudiantes no pudieron ser registrados'
#                     response_data['failed_students'] = failed_students

#                 return Response(response_data, status=status.HTTP_201_CREATED)

#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

#     @swagger_auto_schema(
#         operation_summary="Obtener estudiantes por sesión y clase",
#         operation_description="Obtener lista de estudiantes con su asistencia filtrados por ID de sesión e ID de clase",
#         security=[{'Token': []}],
#         manual_parameters=[
#             openapi.Parameter(
#                 'session_class',
#                 openapi.IN_QUERY,
#                 description="ID de la sesión a consultar",
#                 type=openapi.TYPE_INTEGER,
#                 required=True,
#                 example=1
#             ),
#             openapi.Parameter(
#                 'class_id',
#                 openapi.IN_QUERY,
#                 description="ID de la clase a consultar",
#                 type=openapi.TYPE_INTEGER,
#                 required=True,
#                 example=1
#             )
#         ],
#         responses={
#             200: openapi.Response(
#                 description='Estudiantes obtenidos exitosamente',
#                 examples={
#                     "application/json": {
#                         "students": [
#                             {
#                                 "id": 127,
#                                 "nombre_completo": "Juan Pérez",
#                                 "curso": "Inglés 5 - 7",
#                                 "sesion": 1,
#                                 "fecha_nacimiento": "2010-05-15",
#                                 "asistencia": "PRESENT"
#                             }
#                         ]
#                     }
#                 }
#             ),
#             400: COMMON_RESPONSES[400],
#             404: COMMON_RESPONSES[404],
#             500: COMMON_RESPONSES[500]
#         },
#         tags=["👥 Estudiantes"]
#     )
#     @action(detail=False, methods=['GET'], url_path='getStudents_by_session_class')
#     def get_students_by_session_class(self, request):
#         # Obtener el session_class y class_id desde los parámetros de la consulta
#         session_id = request.query_params.get('session_class', None)
#         class_id = request.query_params.get('class_id', None)

#         if not session_id:
#             return Response({"detail": "El ID de la sesión es requerido."}, status=status.HTTP_400_BAD_REQUEST)

#         if not class_id:
#             return Response({"detail": "El ID de la clase es requerido."}, status=status.HTTP_400_BAD_REQUEST)

#         # Verificar si la sesión existe usando el id_session directamente
#         try:
#             # Intenta primero con el id_session
#             session = Session.objects.get(id_session=session_id, id_class=class_id)
#         except Session.DoesNotExist:
#             try:
#                 # Si no funciona, intentar con num_session 
#                 session = Session.objects.get(num_session=session_id, id_class=class_id)
#             except Session.DoesNotExist:
#                 return Response({"detail": "Sesión no encontrada para esta clase."}, status=status.HTTP_404_NOT_FOUND)

#         # Obtener los registros de asistencia filtrados por la sesión
#         attendance_records = AttendanceStudent.objects.filter(
#             id_session=session.id_session
#         )

#         if not attendance_records.exists():
#             return Response({"detail": "No se encontraron registros de asistencia para esta sesión y clase."}, status=status.HTTP_404_NOT_FOUND)

#         # Obtener los IDs de los estudiantes asociados a esos registros de asistencia
#         student_ids = attendance_records.values_list('id_student', flat=True)

#         # Consultar los estudiantes en la tabla Students usando los IDs
#         students = Students.objects.filter(id__in=student_ids)

#         if not students.exists():
#             return Response({"detail": "Estudiantes no encontrados."}, status=status.HTTP_404_NOT_FOUND)

#         # Obtener la información del curso
#         course = Class.objects.get(id=class_id)

#         # Crear la lista de estudiantes con los campos específicos
#         student_list = []
#         for student in students:
#             # Buscar el registro de asistencia para este estudiante
#             try:
#                 attendance_record = AttendanceStudent.objects.get(
#                     id_student=student.id,
#                     id_session=session.id_session
#                 )
#                 attendance_value = attendance_record.attendance
#             except AttendanceStudent.DoesNotExist:
#                 attendance_value = ""

#             # Crear nombre completo
#             nombre_completo = f"{student.name} {student.last_name}"

#             student_list.append({
#                 "id": student.id,
#                 "nombre_completo": nombre_completo,
#                 "curso": course.name,
#                 "sesion": session.num_session,
#                 "fecha_nacimiento": student.birthdate,
#                 "asistencia": attendance_value
#             })

#         # Respuesta con la información requerida
#         response_data = {
#             "students": student_list
#         }
        
#         return Response(response_data, status=status.HTTP_200_OK)

#     @swagger_auto_schema(
#         operation_summary="Obtener sesiones por clase",
#         operation_description="Obtener lista de sesiones filtradas por ID de clase",
#         security=[{'Token': []}],
#         manual_parameters=[
#             openapi.Parameter(
#                 'class_id',
#                 openapi.IN_QUERY,
#                 description="ID de la clase para filtrar sesiones",
#                 type=openapi.TYPE_INTEGER,
#                 required=True,
#                 example=1
#             )
#         ],
#         responses={
#             200: openapi.Response(
#                 description="Lista de sesiones obtenida exitosamente",
#                 examples={
#                     "application/json": {
#                         "sessions": [
#                             {"id_session": 1, "num_session": 1, "date": "2024-09-10"},
#                             {"id_session": 2, "num_session": 2, "date": "2024-09-11"}
#                         ]
#                     }
#                 }
#             ),
#             400: openapi.Response(
#                 description="Solicitud incorrecta, class_id es requerido",
#                 examples={
#                     "application/json": {
#                         "detail": "El ID de la clase es requerido."
#                     }
#                 }
#             ),
#             404: openapi.Response(
#                 description="No encontrado, no se encontraron sesiones para el class_id dado",
#                 examples={
#                     "application/json": {
#                         "detail": "No se encontraron sesiones para la clase especificada."
#                     }
#                 }
#             ),
#             500: COMMON_RESPONSES[500]
#         },
#         tags=["👥 Estudiantes"]
#     )
#     @action(detail=False, methods=['GET'], url_path='get_sessions_class')
#     def get_sessions_class(self, request):
#         try:
#             class_id = request.query_params.get('class_id', None)

#             if not class_id:
#                 return Response({"detail": "El ID de la clase es requerido."}, status=status.HTTP_400_BAD_REQUEST)

#             # Obtener las sesiones asociadas a esa clase
#             sessions = Session.objects.filter(id_class=class_id).values('id_session', 'num_session', 'date')

#             if not sessions:
#                 return Response({"detail": "No se encontraron sesiones para la clase especificada."}, status=status.HTTP_404_NOT_FOUND)

#             # Convertir el QuerySet a una lista de diccionarios con la estructura deseada
#             session_list = [
#                 {
#                     "id_session": session['id_session'],
#                     "num_session": session['num_session'],
#                     "date": session['date']
#                 }
#                 for session in sessions
#             ]

#             return Response({
#                 "sessions": session_list
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class SupportViewset(ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Enviar mensaje de soporte",
        operation_description="Enviar un mensaje de soporte técnico al administrador del sistema",
        security=[{'Token': []}],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['subject', 'description'],
            properties={
                'subject': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Asunto del mensaje',
                    example='Problema con el sistema de asistencia'
                ),
                'description': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Descripción detallada del problema',
                    example='No puedo actualizar la asistencia de los estudiantes en la clase de Inglés'
                )
            },
        ),
        responses={
            200: openapi.Response(
                description='Mensaje enviado exitosamente',
                examples={
                    "application/json": {
                        "message": "Correo enviado exitosamente."
                    }
                }
            ),
            400: openapi.Response(
                description='Datos requeridos faltantes',
                examples={
                    "application/json": {
                        "error": "El asunto y la descripción son requeridos."
                    }
                }
            ),
            404: openapi.Response(
                description='Voluntario no encontrado',
                examples={
                    "application/json": {
                        "error": "No se encontró el voluntario asociado al usuario."
                    }
                }
            ),
            500: openapi.Response(
                description='Error al enviar el correo',
                examples={
                    "application/json": {
                        "error": "Error al enviar el correo: mensaje de error"
                    }
                }
            ),
            401: COMMON_RESPONSES[401],
            403: COMMON_RESPONSES[403]
        },
        tags=["🛠️ Soporte"]
    )
    @action(detail=False, methods=['POST'], url_path='send_support')
    def send_support(self, request):
        # Obtener el usuario autenticado
        user = request.user

        # Buscar al voluntario relacionado con el usuario
        volunteer = Volunteers.objects.filter(user_id=user.id).first()

        # Verificar si el voluntario existe
        if not volunteer:
            return Response({'error': 'No se encontró el voluntario asociado al usuario.'}, status=404)

        # Obtener el correo electrónico personal del voluntario
        personal_email = user.email

        # Obtener el nombre completo del voluntario
        teacher_name = f"{volunteer.name} {volunteer.last_name}"  # Asumiendo que tienes first_name y last_name en Volunteers

        # Obtener los cursos que dicta el voluntario (usando VolunteerClass como tabla intermedia)
        volunteer_classes = VolunteerClass.objects.filter(id_volunteer=volunteer.id)
        
        # Obtener los nombres de los cursos relacionados con el voluntario
        if volunteer_classes.exists():
            course_ids = volunteer_classes.values_list('id_class', flat=True)
            courses = Class.objects.filter(id__in=course_ids)
            course_list = ', '.join([course.name for course in courses])
        else:
            course_list = 'Sin cursos asignados'

        # Obtener los datos del asunto y la descripción desde el request
        subject = request.data.get('subject', 'Sin asunto')
        description = request.data.get('description', 'Sin descripción')

        if not subject or not description:
            return Response({'error': 'El asunto y la descripción son requeridos.'}, status=400)

        # Correo del administrador al que se enviará el correo
        admin_email = 'maxxd814@gmail.com'  # Cambia esto por el correo real del administrador

        # Construir el mensaje con los detalles adicionales
        message = (
            f"Nombre del Voluntario: {teacher_name}\n"
            f"Correo: {personal_email}\n"
            f"Cursos que dicta: {course_list}\n\n"
            f"Descripción del problema:\n{description}"
        )

        # Enviar el correo
        try:
            send_mail(
                subject=f'Soporte: {subject}',  # Asunto del correo
                message=message,  # Mensaje con detalles adicionales
                from_email=personal_email,  # Remitente (el correo del usuario autenticado)
                recipient_list=[admin_email],  # Destinatario (correo del administrador)
                fail_silently=False,
            )
            return Response({'message': 'Correo enviado exitosamente.'}, status=200)
        except Exception as e:
            return Response({'error': f'Error al enviar el correo: {str(e)}'}, status=500)