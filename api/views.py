from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from .serializers import UserDataSerializer,UserSerializer, GetCourses ,GetStudentsClass ,CourseSerializer ,AttendanceUpdateSerializer , SessionSerializer 
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
from .models import Students , Class ,AttendanceStudent ,Session ,Volunteers ,VolunteerClass ,AuthUserRoles 
from django.core.mail import send_mail
from django.db import transaction

class UserViewSet(ViewSet):
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="User login",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='User password'),
            },
        ),
        responses={200: openapi.Response('OK', UserSerializer)},
        tags=["User Management"]
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
        operation_description="User registration",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='User password'),
            },
        ),
        responses={201: openapi.Response('Created', UserSerializer)},
        tags=["User Management"]
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
        operation_description="Get user profile",
        responses={200: openapi.Response('OK', UserSerializer)},
        tags=["User Management"]
    )
    @action(detail=False, methods=['GET'])
    def profile(self, request):
        serializer = UserSerializer(instance=request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
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
        operation_description="Get list of courses",
        responses={200: openapi.Response('OK', GetCourses)},
        tags=["Courses"]
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
        operation_description="Get list of students filtered by class ID",
        manual_parameters=[
            openapi.Parameter(
                'course_id',
                openapi.IN_QUERY,
                description="ID of the class to filter students",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={200: openapi.Response('OK', GetStudentsClass(many=True))},
        tags=["Courses"]
    )
    @action(detail=False, methods=['GET'], url_path='get_Courses_id')
    def get_schedules_id(self, request):
        course_id = request.query_params.get('course_id', None)
        if not course_id:
            return Response({"detail": "El ID del curso es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        course = get_object_or_404(Class.objects, id=course_id)
        serializer = CourseSerializer(course)
        return Response(serializer.data, status=status.HTTP_200_OK) 
    
    
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
        
class StudentsViewset(ViewSet): 
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get Students",
        responses={200: openapi.Response('OK', GetStudentsClass(many=True))},
        tags=["Students"]
    )
    @action(detail=False, methods=['GET'], url_path='getStudents')
    def get_students(self, request):
        course = Students.objects.all()
        serializer = GetStudentsClass(course,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    #acuerdate desaparecerme
    @swagger_auto_schema(
        operation_description="Get list of students filtered by course ID",
        manual_parameters=[
            openapi.Parameter(
                'class_id',
                openapi.IN_QUERY,
                description="ID of the course to filter students",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={200: openapi.Response('OK', GetStudentsClass(many=True))},
        tags=["Students"]
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
        operation_description="Update attendance statuses for multiple students",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'attendances': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Attendance ID"),
                            'status': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                enum=['ONTIME', 'LATE', 'FAIL'],
                                description="Updated status for the attendance"
                            ),
                        },
                        required=['id', 'status'],
                    ),
                    description="List of attendances to update"
                )
            },
            required=['attendances']
        ),
        responses={
            200: openapi.Response('Attendance statuses updated successfully'),
            400: openapi.Response('Invalid input data')
        },
        tags=["Students"]
    )
    @action(detail=False, methods=['PUT'], url_path='update_statuses_students')
    def update_attendance_statuses(self, request):
        attendances_data = request.data.get('attendances', [])

        if not isinstance(attendances_data, list):
            return Response({'error': 'Invalid data format. Expected a list of attendances.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validamos los datos
        serializer = AttendanceUpdateSerializer(data=attendances_data, many=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        session_number = request.data.get('num_session')
        class_id = request.data.get('id_class')

        updated_attendances = []

        for item in request.data.get('attendances', []):
            # Filtrar por el número de sesión (num_session) y la clase (id_class)
            attendances = AttendanceStudent.objects.filter(
                id_student=item['id'],
                id_session__num_session=session_number,  # Usar la relación con la tabla Session
                id_session__id_class=class_id  # Asegurarse de que la sesión pertenece a la clase correcta
            )
            
            if attendances.exists():
                for attendance in attendances:
                    attendance.attendance = item['attendance']
                    updated_attendances.append(attendance)

        if updated_attendances:
            # Actualizar los registros modificados
            AttendanceStudent.objects.bulk_update(updated_attendances, ['attendance'])

        return Response({'message': 'Attendance statuses updated successfully.'}, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Creates a session for a class and registers attendance for all students.",
        responses={
            201: openapi.Response('Session created successfully and attendance recorded', SessionSerializer),
            403: 'No permission to create sessions for this class or user is not a teacher',
            400: 'Bad request'
        },
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id_class': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the class')
            },
            required=['id_class']
        ),
        tags=['Students']
    )
    @action(detail=False, methods=['POST'], url_path='create_session')
    def create_session(self, request, *args, **kwargs):
        try:
            logged_in_user = request.user.id

            # Consultar los roles del usuario
            user_roles = AuthUserRoles.objects.filter(user_id=logged_in_user).select_related('role')

            # Verificar si el usuario tiene el rol de admin o volunteer
            is_volunteer = user_roles.filter(role__name='Volunteers_Profesor').exists()
            is_admin = user_roles.filter(role__name='admin').exists()

            if not (is_volunteer or is_admin):
                return Response({'error': 'No tienes permisos para realizar esta acción'}, status=status.HTTP_403_FORBIDDEN)

            # Obtener la clase por su ID desde la solicitud
            class_id = request.data.get('id_class')
            if not class_id:
                return Response({'error': 'ID de la clase no proporcionado'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                course_class = Class.objects.get(id=class_id)
            except Class.DoesNotExist:
                return Response({'error': 'Clase no encontrada'}, status=status.HTTP_404_NOT_FOUND)

            volunteer = None  # Inicializar voluntario como None

            if is_volunteer:
                # Verificar si el usuario es un voluntario asociado a esta clase
                try:
                    volunteer = Volunteers.objects.get(user_id=logged_in_user)
                except Volunteers.DoesNotExist:
                    return Response({'error': 'El usuario no es un profesor'}, status=status.HTTP_403_FORBIDDEN)

                if not VolunteerClass.objects.filter(id_class=course_class.id, id_volunteer=volunteer.id).exists():
                    return Response({'error': 'No tienes permiso para crear sesiones en esta clase.'}, status=status.HTTP_403_FORBIDDEN)

            elif is_admin:
                # Si el usuario es admin, buscar el primer voluntario asociado al curso
                volunteer_class = VolunteerClass.objects.filter(id_class=course_class.id).select_related('id_volunteer').first()
                if not volunteer_class:
                    return Response({'error': 'No se encontraron voluntarios asociados a esta clase'}, status=status.HTTP_404_NOT_FOUND)
                volunteer = volunteer_class.id_volunteer

            # Obtener el último número de sesión para la clase dada
            last_session = Session.objects.filter(id_class=course_class).order_by('-num_session').first()
            num_session = (last_session.num_session + 1) if last_session else 1

            # Crear una nueva sesión asociada a la clase
            session = Session.objects.create(
                id_class=course_class,
                num_session=num_session,
                date=timezone.now(),
            )

            # Obtener todos los estudiantes asociados a la clase a través de la tabla intermedia
            students = Students.objects.filter(studentclass__id_class=course_class.id)

            # Registrar la asistencia de cada estudiante
            for student in students:
                AttendanceStudent.objects.create(
                    id_student=student,
                    id_volunteer=volunteer,
                    id_session=session,
                    created_date=timezone.now(),
                    attendance=''  # Puedes cambiar este valor según sea necesario
                )

            # Serializar la nueva sesión creada
            serializer = SessionSerializer(session)

            return Response({
                'message': 'Sesión creada con éxito y asistencia registrada',
                'session': serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(
        operation_description="Get list of students filtered by session ID and class ID",
        manual_parameters=[
            openapi.Parameter(
                'session_class',
                openapi.IN_QUERY,
                description="ID of the session to filter students",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'class_id',
                openapi.IN_QUERY,
                description="ID of the class to filter students",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={200: openapi.Response('OK', GetStudentsClass(many=True))},
        tags=["Students"]
    )
    @action(detail=False, methods=['GET'], url_path='getStudents_by_session_class')
    def get_students_by_session_class(self, request):
        
        # Obtener el session_class y class_id desde los parámetros de la consulta
        session_class = request.query_params.get('session_class', None)
        class_id = request.query_params.get('class_id', None)

        if not session_class:
            return Response({"detail": "El ID de la sesión es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        if not class_id:
            return Response({"detail": "El ID de la clase es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        # Verificar si la sesión pertenece a la clase solicitada
        try:
            session = Session.objects.get(num_session=session_class, id_class=class_id)
        except Session.DoesNotExist:
            return Response({"detail": "Sesión no encontrada para esta clase."}, status=status.HTTP_404_NOT_FOUND)

        # Obtener los registros de asistencia filtrados por la sesión
        attendance_records = AttendanceStudent.objects.filter(
            id_session=session.id_session
        )

        if not attendance_records.exists():
            return Response({"detail": "Estudiantes no encontrados para esta sesión y clase."}, status=status.HTTP_404_NOT_FOUND)

        # Obtener los IDs de los estudiantes asociados a esos registros de asistencia
        student_ids = attendance_records.values_list('id_student', flat=True)

        # Consultar los estudiantes en la tabla Students usando los IDs
        students = Students.objects.filter(id__in=student_ids)

        if not students.exists():
            return Response({"detail": "Estudiantes no encontrados."}, status=status.HTTP_404_NOT_FOUND)

        # Serializar los resultados
        serializer = GetStudentsClass(students, many=True, context={'session_id': session.id_session})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
    operation_description="Get list of sessions filtered by class ID",
    manual_parameters=[
        openapi.Parameter(
            'class_id',
            openapi.IN_QUERY,
            description="ID of the class to filter sessions",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="List of sessions",
            examples={
                "application/json": {
                    "sessions": [
                        {"id_session": 1, "num_session": 101, "date": "2024-09-10"},
                        {"id_session": 2, "num_session": 102, "date": "2024-09-11"}
                    ]
                }
            }
        ),
        400: openapi.Response(
            description="Bad request, class_id is required",
            examples={
                "application/json": {
                    "detail": "El ID de la clase es requerido."
                }
            }
        ),
        404: openapi.Response(
            description="Not found, no sessions found for the given class_id",
            examples={
                "application/json": {
                    "detail": "No se encontraron sesiones para la clase especificada."
                }
            }
        ),
        500: openapi.Response(
            description="Internal server error",
            examples={
                "application/json": {
                    "detail": "Error message"
                }
            }
        )
    },
    tags=["Students"]
)
    @action(detail=False, methods=['GET'], url_path='get_sessions_class')
    def get_sessions_class(self, request):
        try:
            class_id = request.query_params.get('class_id', None)

            if not class_id:
                return Response({"detail": "El ID de la clase es requerido."}, status=status.HTTP_400_BAD_REQUEST)

            # Obtener las sesiones asociadas a esa clase
            sessions = Session.objects.filter(id_class=class_id).values('id_session', 'num_session', 'date')

            if not sessions:
                return Response({"detail": "No se encontraron sesiones para la clase especificada."}, status=status.HTTP_404_NOT_FOUND)

            # Convertir el QuerySet a una lista de diccionarios con la estructura deseada
            session_list = [
                {
                    "id_session": session['id_session'],
                    "num_session": session['num_session'],
                    "date": session['date']
                }
                for session in sessions
            ]

            return Response({
                "sessions": session_list
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class SupportViewset(ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['POST'], url_path='send_support', permission_classes=[])
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