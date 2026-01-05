from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from .serializers import SessionSerializer,UserDataSerializer,UserSerializer, GetCourses ,CourseSerializer  ,GetStudentsClass
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import  Courses ,Volunteers, VolunteerCourses ,Students , AttendanceStudent, Session , AuthUserRoles, AuthUser
from django.core.mail import send_mail
from django.db import transaction, connection


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

# Respuestas comunes simplificadas
COMMON_RESPONSES = {
    400: "Datos inválidos",
    401: "No autorizado", 
    403: "Acceso prohibido",
    404: "No encontrado",
    500: "Error del servidor"
}

class UserViewSet(ViewSet):
    
    authentication_classes = [TokenAuthentication]
    permission_classes = []
    
    @swagger_auto_schema(
        operation_summary="Login de usuario",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, example='admin@slperu.com'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, example='adminslperu'),
            },
        ),
        responses={200: "Login exitoso", 400: COMMON_RESPONSES[400], 403: COMMON_RESPONSES[403], 404: COMMON_RESPONSES[404]},
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
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, example='nuevo@ejemplo.com'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, example='password123'),
            },
        ),
        responses={201: "Usuario creado", 400: COMMON_RESPONSES[400], 500: COMMON_RESPONSES[500]},
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
        responses={200: UserSerializer, 401: COMMON_RESPONSES[401], 403: COMMON_RESPONSES[403]},
        tags=["🔐 Autenticación"]
    )
    @action(detail=False, methods=['GET'])
    def profile(self, request):
        serializer = UserSerializer(instance=request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_summary="Información del usuario",
        manual_parameters=[
            openapi.Parameter('id_user', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True)
        ],
        responses={200: UserDataSerializer(many=True), 400: COMMON_RESPONSES[400], 404: COMMON_RESPONSES[404], 500: COMMON_RESPONSES[500]},
        tags=["🔐 Autenticación"]
    )
    def list(self, request):
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
                   
class CoursesViewSet(ViewSet):
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Obtener todos los cursos",
        responses={200: GetCourses(many=True), 401: COMMON_RESPONSES[401], 403: COMMON_RESPONSES[403]},
        tags=["📚 Cursos"]
    )
    # @action(detail=False, methods=['GET'], url_path='list')
    def list(self, request):
        """Obtener todos los cursos disponibles: Incluido estudiantes matriculados"""
        try:
            courses = Courses.objects.all().order_by('-created_at')
            serializer = GetCourses(courses, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Crear nuevo curso",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'day', 'start_time', 'end_time'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, example='Matemáticas Básicas'),
                'day': openapi.Schema(type=openapi.TYPE_STRING, example='Lunes'),
                'start_time': openapi.Schema(type=openapi.TYPE_STRING, example='09:00:00'),
                'end_time': openapi.Schema(type=openapi.TYPE_STRING, example='11:00:00'),
                'color': openapi.Schema(type=openapi.TYPE_STRING, example='#FF5733'),
                'status': openapi.Schema(type=openapi.TYPE_INTEGER, example=1)
            },
        ),
        responses={201: CourseSerializer, 400: COMMON_RESPONSES[400], 500: COMMON_RESPONSES[500]},
        tags=["📚 Cursos"]
    )
    # @action(detail=False, methods=['POST'], url_path='create')
    def create(self, request):
        """Crear un nuevo curso"""
        try:
            serializer = CourseSerializer(data=request.data)
            if serializer.is_valid():
                course = serializer.save()
                return Response(CourseSerializer(course).data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Obtener curso por ID",
        responses={200: CourseSerializer, 400: COMMON_RESPONSES[400], 404: COMMON_RESPONSES[404], 500: COMMON_RESPONSES[500]},
        tags=["📚 Cursos"]
    )
    def retrieve(self, request, pk=None):
        """Obtener un curso específico por ID"""
        try:
            course = get_object_or_404(Courses, id=pk)
            serializer = CourseSerializer(course)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Actualizar curso",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, example='Matemáticas Avanzadas'),
                'day': openapi.Schema(type=openapi.TYPE_STRING, example='Martes'),
                'start_time': openapi.Schema(type=openapi.TYPE_STRING, example='10:00:00'),
                'end_time': openapi.Schema(type=openapi.TYPE_STRING, example='12:00:00'),
                'color': openapi.Schema(type=openapi.TYPE_STRING, example='#00FF00'),
                'status': openapi.Schema(type=openapi.TYPE_INTEGER, example=1)
            },
        ),
        responses={200: CourseSerializer, 400: COMMON_RESPONSES[400], 404: COMMON_RESPONSES[404], 500: COMMON_RESPONSES[500]},
        tags=["📚 Cursos"]
    )
    def update(self, request, pk=None):
        """Actualizar un curso existente"""
        if not pk:
            return Response({"detail": "El ID del curso es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            course = get_object_or_404(Courses, id=pk)
            serializer = CourseSerializer(course, data=request.data, partial=True)
            if serializer.is_valid():
                course = serializer.save()
                return Response(CourseSerializer(course).data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Eliminar curso",
        responses={200: "Curso eliminado", 400: COMMON_RESPONSES[400], 404: COMMON_RESPONSES[404], 500: COMMON_RESPONSES[500]},
        tags=["📚 Cursos"]
    )
    def destroy(self, request, pk=None):
        """Eliminar un curso"""
        if not pk:
            return Response({"detail": "El ID del curso es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            course = get_object_or_404(Courses, id=pk)
            course_name = course.name
            course.delete()
            return Response({"detail": f"Curso '{course_name}' eliminado exitosamente."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Obtener cursos por usuario y rol",
        manual_parameters=[
            openapi.Parameter('user_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
            openapi.Parameter('role_id', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True)
        ],
        responses={200: GetCourses(many=True), 400: COMMON_RESPONSES[400], 500: COMMON_RESPONSES[500]},
        tags=["📚 Cursos"]
    )
    @action(detail=False, methods=['GET'], url_path='get_courses')
    def get_courses_by_user_and_role(self, request):
        """Obtener cursos filtrados por usuario y rol"""
        user_id = request.query_params.get('user_id')
        role_id = request.query_params.get('role_id')
    
        if user_id is None or role_id is None:
            return Response({"detail": "user_id and role_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verificar si el usuario tiene el rol de coordinador (suponiendo que 1 es el ID del coordinador)
            is_coordinator = (role_id == "1")

            if is_coordinator:
                # Si el usuario es coordinador, retornar todos los cursos
                courses = Courses.objects.all()
            else:
                # Si el usuario no es coordinador, retornar solo los cursos asociados
                # Obtener el ID del voluntario asociado al usuario
                volunteer = Volunteers.objects.get(user_id=user_id)

                # Filtrar cursos basados en el ID del voluntario
                courses = Courses.objects.filter(
                    volunteerclass__id_volunteer=volunteer.id
                ).distinct()  # Asegúrate de no obtener duplicados

        except Volunteers.DoesNotExist:
            # Si el usuario no es un voluntario, no devolver cursos
            courses = Courses.objects.none()
            print("No volunteer found for this user.")
        except Exception as e:
            # Manejar cualquier otra excepción
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        course_serializer = GetCourses(courses, many=True)
        return Response(course_serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Actualizar color del curso",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['class_id', 'color'],
            properties={
                'class_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                'color': openapi.Schema(type=openapi.TYPE_STRING, example='#FF5733'),
            },
        ),
        responses={200: "Color actualizado", 400: COMMON_RESPONSES[400], 404: COMMON_RESPONSES[404], 500: COMMON_RESPONSES[500]},
        tags=["📚 Cursos"]
    )
    @action(detail=False, methods=['POST'], url_path='update_color')
    def update_color(self, request):
        """Actualizar solo el color de un curso"""
        class_id = request.data.get('class_id')
        color = request.data.get('color')
        
        if not class_id or not color:
            return Response({"detail": "class_id and color are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Obtener la clase por ID
            class_obj = Courses.objects.get(id=class_id)
            
            # Actualizar el color de la clase
            class_obj.color = color
            class_obj.save()

            return Response({"detail": "Color updated successfully."}, status=status.HTTP_200_OK)
        
        except Courses.DoesNotExist:
            return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Crear nueva sesión para curso",
        operation_description="Crear una nueva sesión para un curso específico. Los estudiantes se registran automáticamente con asistencia en blanco.",
        security=[{'Token': []}],
        responses={
            201: openapi.Response(
                description='Sesión creada exitosamente',
                examples={
                    "application/json": {
                        "message": "Sesión creada con éxito y asistencia registrada en blanco",
                        "session": {
                            "id_session": 4,
                            "id_course": 1,
                            "num_session": 2,
                            "date": "2025-05-08T04:15:30Z"
                        },
                        "student_count": 15
                    }
                }
            ),
            400: openapi.Response(
                description='Error en la solicitud',
                examples={
                    "application/json": {
                        "error": "No hay estudiantes asociados a esta clase. No se puede crear una sesión.",
                        "status": "EMPTY_CLASS"
                    }
                }
            ),
            401: COMMON_RESPONSES[401],
            403: COMMON_RESPONSES[403],
            404: COMMON_RESPONSES[404]
        },
        tags=["📚 Cursos"]
    )
    @action(detail=True, methods=['POST'], url_path='session')
    def create_session(self, request, pk=None):
        """Crear una nueva sesión para un curso específico"""
        try:
            # 1) Tomar el User de Django desde request.user
            django_user = request.user

            # 2) Traducir ese User de Django a mi modelo AuthUser
            try:
                auth_user = AuthUser.objects.get(username=django_user.username)
            except AuthUser.DoesNotExist:
                return Response(
                    {"error": "No se encontró el AuthUser correspondiente a este usuario."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # 3) Verificar roles
            user_roles = AuthUserRoles.objects.filter(user=django_user).select_related('role')
            is_volunteer = user_roles.filter(role__name='Volunteers_Profesor').exists()
            is_admin = user_roles.filter(role__name='Admin').exists()
            
            if not (is_volunteer or is_admin):
                return Response(
                    {'error': 'No tienes permisos para realizar esta acción.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # 4) Usar pk del path como course_id
            course_id = pk
            if not course_id:
                return Response(
                    {'error': 'ID del curso no proporcionado.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 5) Obtener el curso; si no existe, 404
            try:
                course = Courses.objects.get(id=course_id)
            except Courses.DoesNotExist:
                return Response({'error': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

            # 6) Verificar que al menos haya 1 estudiante en esa clase
            # student_count = Students.objects.filter(course_enrollments__id_course=course.id).count()
            # if student_count == 0:
            #     return Response({
            #         'error': 'No hay estudiantes asociados a este curso. No se puede crear una sesión.',
            #         'status': 'EMPTY_CLASS'
            #     }, status=status.HTTP_400_BAD_REQUEST)

            # 7) Determinar qué voluntario crea la sesión
            volunteer = None
            
            # Primero verificar si se proporcionó un volunteer_id en el request
            volunteer_id = request.data.get('volunteer_id')
            if volunteer_id:
                try:
                    volunteer = Volunteers.objects.get(id=volunteer_id, status=1)
                except Volunteers.DoesNotExist:
                    return Response({'error': 'El voluntario especificado no existe o no está activo.'}, status=status.HTTP_400_BAD_REQUEST)
            elif is_volunteer:
                try:
                    volunteer = Volunteers.objects.get(user=auth_user)
                except Volunteers.DoesNotExist:
                    return Response({'error': 'El usuario no es un profesor.'}, status=status.HTTP_403_FORBIDDEN)

                # Confirmar que ese voluntario está asignado al curso
                if not VolunteerCourses.objects.filter(id_course=course.id, id_volunteer=volunteer.id).exists():
                    return Response(
                        {'error': 'No tienes permiso para crear sesiones en este curso.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            else:
                # Si es admin, tomar el primer voluntario que esté asignado al curso (si existe)
                # Ahora permitimos crear sesiones sin voluntarios
                vc = VolunteerCourses.objects.filter(id_course=course.id).select_related('id_volunteer').first()
                if vc:
                    volunteer = vc.id_volunteer
                # Si no hay voluntarios, volunteer quedará como None y se asignará después

            # 8) Obtener fecha y volunteer_id del request
            session_date = request.data.get('date')
            volunteer_id = request.data.get('volunteer_id')  # Obtener volunteer_id del frontend
            
            if session_date:
                try:
                    # Intentar parsear la fecha proporcionada
                    from datetime import datetime
                    session_date = datetime.fromisoformat(session_date.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    # Si hay error en el formato, usar fecha actual
                    session_date = timezone.now()
            else:
                session_date = timezone.now()

            # Si se proporciona volunteer_id, verificar que exista
            # Los voluntarios son libres, no están atados a ningún curso
            volunteer_instance = None
            if volunteer_id:
                try:
                    volunteer_instance = Volunteers.objects.get(id=volunteer_id)
                except Volunteers.DoesNotExist:
                    return Response(
                        {'error': 'El voluntario seleccionado no existe.'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            elif volunteer:  # Si no se envió volunteer_id pero ya había uno asignado
                volunteer_instance = volunteer

            # 9) Calcular el próximo num_session
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT MAX(num_session) FROM sessions WHERE id_course = %s",
                    [course.id]
                )
                result = cursor.fetchone()[0]
                num_session = (result + 1) if result else 1

            # 10) Crear la sesión y los registros de asistencia
            with transaction.atomic():
                session = Session.objects.create(
                    id_course=course,
                    id_volunteer=volunteer_instance,  # Guardar el voluntario en la sesión
                    num_session=num_session,
                    date=session_date,
                )

                students = Students.objects.filter(course_enrollments__id_course=course.id)
                # Solo crear registros de asistencia si hay un voluntario asignado
                if volunteer_instance:
                    attendance_records = []
                    for student in students:
                        attendance_records.append(
                            AttendanceStudent(
                                id_student=student,
                                id_volunteer=volunteer_instance,
                                id_session=session,
                                created_date=timezone.now(),
                                attendance=""  
                            )
                        )
                    if attendance_records:
                        AttendanceStudent.objects.bulk_create(attendance_records)

                serializer = SessionSerializer(session)
                return Response({
                    'message': 'Sesión creada con éxito.' + (' Asistencia registrada en blanco.' if volunteer_instance else ' Los estudiantes se agregarán después.'),
                    'session': serializer.data
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"Error en create_session: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Obtener sesión específica de un curso",
        operation_description="Obtener información detallada de una sesión específica de un curso (incluido: estudiantes)",
        security=[{'Token': []}],
        responses={
            200: openapi.Response(
                description="Sesión obtenida exitosamente",
                examples={
                    "application/json": {
                        "id_session": 1,
                        "num_session": 1,
                        "date": "2024-09-10",
                        "id_course": 1
                    }
                }
            ),
            404: openapi.Response(
                description="Sesión no encontrada",
                examples={
                    "application/json": {
                        "detail": "Sesión no encontrada para este curso."
                    }
                }
            ),
            500: COMMON_RESPONSES[500]
        },
        tags=["📚 Cursos"]
    )
    @action(detail=True, methods=['GET'], url_path='session/(?P<session_id>[^/.]+)')
    def get_session(self, request, pk=None, session_id=None):
        """Obtener una sesión específica de un curso"""
        try:
            # pk contiene el course_id, session_id viene del path
            course_id = pk
            if not course_id:
                return Response(
                    {'error': 'ID del curso no proporcionado.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not session_id:
                return Response(
                    {'error': 'ID de sesión no proporcionado.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verificar que el curso existe
            try:
                course = Courses.objects.get(id=course_id)
            except Courses.DoesNotExist:
                return Response(
                    {'error': 'Curso no encontrado.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Buscar la sesión por id_session o num_session
            try:
                # Intentar primero con id_session
                session = Session.objects.get(id_session=session_id, id_course=course_id)
            except Session.DoesNotExist:
                try:
                    # Si no funciona, intentar con num_session
                    session = Session.objects.get(num_session=session_id, id_course=course_id)
                except Session.DoesNotExist:
                    return Response(
                        {'detail': 'Sesión no encontrada para este curso.'},
                        status=status.HTTP_404_NOT_FOUND
                    )

            # Serializar y devolver la sesión
            serializer = SessionSerializer(session)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error en get_session: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Obtener todas las sesiones de un curso",
        operation_description="Obtener lista completa de sesiones de un curso específico ordenadas por número de sesión",
        security=[{'Token': []}],
        responses={
            200: openapi.Response(
                description="Sesiones obtenidas exitosamente",
                examples={
                    "application/json": {
                        "sessions": [
                            {
                                "id_session": 1,
                                "id_course": 1,
                                "num_session": 1,
                                "date": "2024-09-10T10:00:00Z"
                            },
                            {
                                "id_session": 2,
                                "id_course": 1,
                                "num_session": 2,
                                "date": "2024-09-17T10:00:00Z"
                            }
                        ],
                        "total": 2
                    }
                }
            ),
            404: openapi.Response(
                description="Curso no encontrado",
                examples={
                    "application/json": {
                        "error": "Curso no encontrado."
                    }
                }
            ),
            500: COMMON_RESPONSES[500]
        },
        tags=["📚 Cursos"]
    )
    @action(detail=True, methods=['GET'], url_path='sessions')
    def get_all_sessions(self, request, pk=None):
        """Obtener todas las sesiones de un curso específico"""
        try:
            # pk contiene el course_id
            course_id = pk
            if not course_id:
                return Response(
                    {'error': 'ID del curso no proporcionado.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verificar que el curso existe
            try:
                course = Courses.objects.get(id=course_id)
            except Courses.DoesNotExist:
                return Response(
                    {'error': 'Curso no encontrado.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Obtener todas las sesiones del curso ordenadas por num_session
            sessions = Session.objects.filter(id_course=course_id).order_by('num_session')

            # Serializar las sesiones
            serializer = SessionSerializer(sessions, many=True)
            
            return Response({
                'sessions': serializer.data,
                'total': sessions.count()
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error en get_all_sessions: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Actualizar estado de asistencia",
        operation_description="Actualizar el estado de asistencia para múltiples estudiantes en una sesión específica",
        security=[{'Token': []}],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['attendances', 'num_session', 'id_course'],
            properties={
                'attendances': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description="Lista de asistencias a actualizar",
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=['id', 'attendance'],
                        properties={
                            'id': openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                description="ID del estudiante",
                                example=127
                            ),
                            'attendance': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                enum=['PRESENT', 'TARDY', 'ABSENT', 'JUSTIFIED', ''],
                                description="Estado de asistencia (PRESENT=Presente, TARDY=Tardanza, ABSENT=Falta, JUSTIFIED=Justificado, ''=No registrado)",
                                example="PRESENT"
                            ),
                        },
                    )
                ),
                'num_session': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Número de sesión",
                    example=1
                ),
                'id_course': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID del curso",
                    example=1
                )
            },
        ),
        responses={
            200: openapi.Response(
                description='Estados de asistencia actualizados exitosamente',
                examples={
                    "application/json": {
                        "message": "Attendance statuses updated successfully.",
                    }
                }
            ),
            400: openapi.Response(
                description='Datos de entrada inválidos',
                examples={
                    "application/json": {
                        "error": "Valor de asistencia no válido. Valores permitidos: PRESENT, TARDY, ABSENT, JUSTIFIED, "
                    }
                }
            ),
            401: COMMON_RESPONSES[401],
            403: COMMON_RESPONSES[403]
        },
        tags=["📚 Cursos"]
    )
    @action(detail=False, methods=['PUT'], url_path='update_statuses_students')
    def update_attendance_statuses(self, request):
        attendances_data = request.data.get('attendances', [])

        if not isinstance(attendances_data, list):
            return Response({'error': 'Invalid data format. Expected a list of attendances.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validar los valores de asistencia
        valid_attendance_values = ['PRESENT', 'TARDY', 'ABSENT', 'JUSTIFIED', '']
        for item in attendances_data:
            if 'attendance' not in item or item['attendance'] not in valid_attendance_values:
                return Response(
                    {'error': f'Valor de asistencia no válido. Valores permitidos: {", ".join(valid_attendance_values)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        session_number = request.data.get('num_session')
        class_id = request.data.get('id_course') or request.data.get('id_class')

        if not session_number or not class_id:
            return Response({'error': 'Session number and class ID are required.'}, status=status.HTTP_400_BAD_REQUEST)

        updated_attendances = []

        for item in attendances_data:
            # Filtrar por el número de sesión (num_session) y la clase (id_course)
            attendances = AttendanceStudent.objects.filter(
                id_student=item['id'],
                id_session__num_session=session_number,  # Usar la relación con la tabla Session
                id_session__id_course=class_id  # Asegurarse de que la sesión pertenece a la clase correcta
            )
            
            if attendances.exists():
                for attendance in attendances:
                    attendance.attendance = item['attendance']
                    updated_attendances.append(attendance)

        if updated_attendances:
            # Actualizar los registros modificados
            AttendanceStudent.objects.bulk_update(updated_attendances, ['attendance'])

        return Response({
            'message': 'Attendance statuses updated successfully.',
            'attendance_legend': {
                'PRESENT': 'Presente',
                'TARDY': 'Tardanza',
                'ABSENT': 'Falta',
                'JUSTIFIED': 'Justificado',
                '': 'No registrado'
            }
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_summary="Agregar estudiante a sesión",
        operation_description="Agrega un estudiante a una sesión existente creando un registro de asistencia",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['student_id', 'session_id'],
            properties={
                'student_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID del estudiante a agregar",
                    example=1
                ),
                'session_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID de la sesión",
                    example=1
                )
            }
        ),
        responses={
            201: openapi.Response(
                description='Estudiante agregado exitosamente',
                examples={
                    "application/json": {
                        "message": "Estudiante agregado a la sesión exitosamente",
                        "attendance_id": 123
                    }
                }
            ),
            400: COMMON_RESPONSES[400],
            404: COMMON_RESPONSES[404],
            500: COMMON_RESPONSES[500]
        },
        tags=["📚 Cursos"]
    )
    @action(detail=False, methods=['POST'], url_path='add_student_to_session')
    def add_student_to_session(self, request):
        """Agregar un estudiante a una sesión existente"""
        student_id = request.data.get('student_id')
        session_id = request.data.get('session_id')
        
        if not student_id or not session_id:
            return Response(
                {"detail": "student_id y session_id son requeridos."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Verificar que el estudiante existe
            student = Students.objects.get(id=student_id)
            
            # Verificar que la sesión existe
            session = Session.objects.get(id_session=session_id)
            
            # Verificar si el estudiante ya está en la sesión
            existing_attendance = AttendanceStudent.objects.filter(
                id_student=student,
                id_session=session
            ).first()
            
            if existing_attendance:
                return Response(
                    {"detail": "El estudiante ya está registrado en esta sesión."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Obtener un voluntario asignado al curso de la sesión
            course = session.id_course
            volunteer_course = VolunteerCourses.objects.filter(id_course=course).first()
            volunteer = volunteer_course.id_volunteer if volunteer_course else None
            
            if not volunteer:
                # Si no hay voluntario, buscar cualquier voluntario activo
                from api.models import Volunteers
                volunteer = Volunteers.objects.filter(status=1).first()
            
            # Si aún no hay voluntario disponible, devolver error
            if not volunteer:
                return Response(
                    {"detail": "No hay voluntarios disponibles. Por favor, registre un voluntario primero."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crear el registro de asistencia sin marcar (vacío)
            attendance = AttendanceStudent.objects.create(
                id_student=student,
                id_volunteer=volunteer,
                id_session=session,
                created_date=timezone.now(),
                attendance=""
            )
            
            return Response({
                "message": "Estudiante agregado a la sesión exitosamente",
                "attendance_id": attendance.id,
                "student": {
                    "id": student.id,
                    "name": f"{student.name} {student.last_name}",
                    "birthdate": student.birthdate
                }
            }, status=status.HTTP_201_CREATED)
            
        except Students.DoesNotExist:
            return Response(
                {"detail": "Estudiante no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Session.DoesNotExist:
            return Response(
                {"detail": "Sesión no encontrada."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": f"Error al agregar estudiante: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
class ClassViewset(ViewSet): 
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Obtener todos los estudiantes",
        operation_description="Obtener lista completa de estudiantes registrados",
        security=[{'Token': []}],
        responses={
            200: openapi.Response(
                description='Lista de estudiantes obtenida exitosamente',
                schema=GetStudentsClass(many=True)
            ),
            401: COMMON_RESPONSES[401],
            403: COMMON_RESPONSES[403]
        },
        tags=["👥 Dummy"]
    )
    @action(detail=False, methods=['GET'], url_path='getStudents')
    def get_students(self, request):
        course = Students.objects.all()
        serializer = GetStudentsClass(course,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Obtener estudiantes por clase",
        operation_description="Obtener lista de estudiantes filtrados por ID de clase",
        security=[{'Token': []}],
        manual_parameters=[
            openapi.Parameter(
                'class_id',
                openapi.IN_QUERY,
                description="ID de la clase para filtrar estudiantes",
                type=openapi.TYPE_INTEGER,
                required=True,
                example=1
            )
        ],
        responses={
            200: openapi.Response(
                description='Estudiantes de la clase obtenidos exitosamente',
                schema=GetStudentsClass(many=True)
            ),
            400: COMMON_RESPONSES[400],
            404: COMMON_RESPONSES[404],
            500: COMMON_RESPONSES[500]
        },
        tags=["👥 Dummy"]
    )
    @action(detail=False, methods=['GET'], url_path='getStudents_id')
    def get_students_id(self, request):
        try:
            class_id = request.query_params.get('class_id', None)

            if not class_id:
                return Response({"detail": "El ID de la clase es requerido."}, status=status.HTTP_400_BAD_REQUEST)

            # Obtenemos los estudiantes que pertenecen a una clase específica
            resultados = Students.objects.filter(
                studentclass__id_class=class_id
            )

            if not resultados.exists():
                return Response({"detail": "Estudiantes no encontrados."}, status=status.HTTP_404_NOT_FOUND)

            # Serializar los resultados
            serializer = GetStudentsClass(resultados, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Obtener estudiantes por sesión y clase",
        operation_description="Obtener lista de estudiantes con su asistencia filtrados por ID de sesión e ID de clase",
        security=[{'Token': []}],
        manual_parameters=[
            openapi.Parameter(
                'session_class',
                openapi.IN_QUERY,
                description="ID de la sesión a consultar",
                type=openapi.TYPE_INTEGER,
                required=True,
                example=1
            ),
            openapi.Parameter(
                'class_id',
                openapi.IN_QUERY,
                description="ID de la clase a consultar",
                type=openapi.TYPE_INTEGER,
                required=True,
                example=1
            )
        ],
        responses={
            200: openapi.Response(
                description='Estudiantes obtenidos exitosamente',
                examples={
                    "application/json": {
                        "students": [
                            {
                                "id": 127,
                                "nombre_completo": "Juan Pérez",
                                "curso": "Inglés 5 - 7",
                                "sesion": 1,
                                "fecha_nacimiento": "2010-05-15",
                                "asistencia": "PRESENT"
                            }
                        ]
                    }
                }
            ),
            400: COMMON_RESPONSES[400],
            404: COMMON_RESPONSES[404],
            500: COMMON_RESPONSES[500]
        },
        tags=["👥 Dummy"]
    )
    @action(detail=False, methods=['GET'], url_path='getStudents_by_session_class')
    def get_students_by_session_class(self, request):
        # Obtener el session_class y class_id desde los parámetros de la consulta
        session_id = request.query_params.get('session_class', None)
        class_id = request.query_params.get('class_id', None)

        if not session_id:
            return Response({"detail": "El ID de la sesión es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        if not class_id:
            return Response({"detail": "El ID de la clase es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        # Verificar si la sesión existe usando el id_session directamente
        try:
            # Intenta primero con el id_session
            session = Session.objects.get(id_session=session_id, id_course=class_id)
        except Session.DoesNotExist:
            try:
                # Si no funciona, intentar con num_session 
                session = Session.objects.get(num_session=session_id, id_course=class_id)
            except Session.DoesNotExist:
                return Response({"detail": "Sesión no encontrada para esta clase."}, status=status.HTTP_404_NOT_FOUND)

        # Obtener los registros de asistencia filtrados por la sesión
        attendance_records = AttendanceStudent.objects.filter(
            id_session=session.id_session
        )

        # if not attendance_records.exists():
        #     return Response({"detail": "No se encontraron registros de asistencia para esta sesión y clase."}, status=status.HTTP_404_NOT_FOUND)

        # Obtener los IDs de los estudiantes asociados a esos registros de asistencia
        student_ids = attendance_records.values_list('id_student', flat=True)

        # Consultar los estudiantes en la tabla Students usando los IDs
        students = Students.objects.filter(id__in=student_ids)

        # if not students.exists():
        #     return Response({"detail": "Estudiantes no encontrados."}, status=status.HTTP_404_NOT_FOUND)

        # Obtener la información del curso
        course = Courses.objects.get(id=class_id)

        # Crear la lista de estudiantes con los campos específicos
        student_list = []
        for student in students:
            # Buscar el registro de asistencia para este estudiante
            try:
                attendance_record = AttendanceStudent.objects.get(
                    id_student=student.id,
                    id_session=session.id_session
                )
                attendance_value = attendance_record.attendance
            except AttendanceStudent.DoesNotExist:
                attendance_value = ""

            # Crear nombre completo
            nombre_completo = f"{student.name} {student.last_name}"

            student_list.append({
                "id": student.id,
                "nombre_completo": nombre_completo,
                "curso": course.name,
                "sesion": session.num_session,
                "fecha_nacimiento": student.birthdate,
                "asistencia": attendance_value
            })

        # Respuesta con la información requerida
        response_data = {
            "students": student_list
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
 
class SupportViewset(ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Enviar mensaje de soporte",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['subject', 'description'],
            properties={
                'subject': openapi.Schema(type=openapi.TYPE_STRING, example='Problema con asistencia'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, example='No puedo actualizar asistencia')
            },
        ),
        responses={200: "Mensaje enviado", 400: COMMON_RESPONSES[400], 404: COMMON_RESPONSES[404], 500: COMMON_RESPONSES[500]},
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
        volunteer_classes = VolunteerCourses.objects.filter(id_volunteer=volunteer.id)
        
        # Obtener los nombres de los cursos relacionados con el voluntario
        if volunteer_classes.exists():
            course_ids = volunteer_classes.values_list('id_course', flat=True)
            courses = Courses.objects.filter(id__in=course_ids)
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