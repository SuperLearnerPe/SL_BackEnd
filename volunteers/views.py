from django.core.mail import send_mail
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from .serializers import GetVolunteersSerializer,UserAuthSerializer ,VolunteerSerializer
from rest_framework import status
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from django.contrib.auth.hashers import make_password
from django.utils import timezone
# from django.contrib.auth.models import User
from api.models import Volunteers ,AuthUser , AuthRole , AuthUserRoles ,Class ,VolunteerClass
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

class VolunteersViewSet(ViewSet):
    
    @action(detail=False, methods=['GET'], url_path='Get_Volunteers')
    def Get_Volunteers(self, request):
        try:
            # Obtener todos los voluntarios
            volunteers = Volunteers.objects.all().order_by("-id")

            # Serializar los voluntarios
            serializer = GetVolunteersSerializer(volunteers, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['POST'], url_path='create_volunteer')
    def create_volunteer(self, request):
        User = get_user_model()  
        user_data = request.data.get('user')
        volunteer_data = request.data.get('volunteer')
        course_ids = request.data.get('course_ids', [])

        if not user_data or not volunteer_data:
            return Response({"error": "Se requiere tanto la información del usuario como la del voluntario."}, status=status.HTTP_400_BAD_REQUEST)

        # Validar los datos del usuario
        user_serializer = UserAuthSerializer(data=user_data)
        if not user_serializer.is_valid():
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

        user_data['date_joined'] = timezone.now()
        user_data['is_active'] = user_data.get('is_active', True)

        # Crear el usuario usando el modelo AuthUser
        user = User.objects.create_user(**user_data)

        # Crear el token para el nuevo usuario
        token, created = Token.objects.get_or_create(user=user)

        # Aquí debes agregar el rol
        role_id = volunteer_data.pop('role', None)

        volunteer_data['user'] = user.id
        volunteer_serializer = VolunteerSerializer(data=volunteer_data)

        if not volunteer_serializer.is_valid():
            return Response(volunteer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Crear el voluntario
        volunteer = volunteer_serializer.save()

        if role_id:
            try:
                role = AuthRole.objects.get(id=role_id)
                AuthUserRoles.objects.create(user=user, role=role)
            except AuthRole.DoesNotExist:
                return Response({"error": f"Rol con ID {role_id} no existe."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Serializar de nuevo el usuario ya creado
        user_serializer = UserAuthSerializer(user)

        if course_ids:  # Verificamos que sea una lista no vacía
            valid_courses = []
            for course_id in course_ids:
                try:
                    class_instance = Class.objects.get(id=course_id)
                    VolunteerClass.objects.create(id_class=class_instance, id_volunteer=volunteer)
                    valid_courses.append(class_instance.name)  # Añadir el nombre del curso a una lista
                except Class.DoesNotExist:
                    return Response({"error": f"Curso con ID {course_id} no existe."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            valid_courses = None
    
        personal_email = volunteer_data.get('personal_email') 
        subject = 'Bienvenido a SuperLearner'
        message = f'Hola {user_data["first_name"]},\n\nTu cuenta ha sido creada con éxito. Estos son tus datos de acceso:\n\nUsuario: {user_data["username"]}\nCorreo Institucional: {user_data["email"]}\nContraseña: {user_data["password"]}\n\nGracias por registrarte.'
        send_mail(
            subject,
            message,
            'admin@superlearner.org',  
            [personal_email],  
            fail_silently=False,
        )

        return Response({
            'user': user_serializer.data,
            'volunteer': volunteer_serializer.data,
            'courses': valid_courses, 
            'token': token.key
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['PUT'], url_path='update_volunteer')
    def update_volunteer(self, request, pk=None):
        # Obtener los datos enviados por el frontend
        volunteer_id = request.data.get('volunteer_id')
        user_id = request.data.get('user_id')
        user_data = request.data.get('user')
        volunteer_data = request.data.get('volunteer', {})
        course_ids = request.data.get('course_ids', []) 

        # Validar que los IDs y los datos estén presentes
        if not volunteer_id or not user_id or not user_data:
            return Response({"error": "Se requiere el id del usuario, id del voluntario, y la información del usuario."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Obtener el voluntario basado en el `volunteer_id`
            volunteer = Volunteers.objects.get(pk=volunteer_id)
        except Volunteers.DoesNotExist:
            return Response({"error": "El voluntario no existe."}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Obtener el usuario basado en el `user_id`
            user = AuthUser.objects.get(id=user_id)
        except AuthUser.DoesNotExist:
            return Response({"error": "El usuario no existe."}, status=status.HTTP_404_NOT_FOUND)

        # Actualizar el email del usuario si se proporciona en user_data
        if 'email' in user_data:
            # Verificar que el nuevo email no esté ya en uso por otro usuario
            if AuthUser.objects.filter(email=user_data['email']).exclude(id=user_id).exists():
                return Response({"error": "El email ya está en uso por otro usuario."}, status=status.HTTP_400_BAD_REQUEST)
            user.email = user_data['email']
            user.save(update_fields=['email'])

        # Serializar los datos del usuario para actualizarlos
        user_serializer = UserAuthSerializer(user, data=user_data, partial=True)  # Partial permite actualizar campos individuales
        if not user_serializer.is_valid():
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Si la contraseña está presente, hashearla
        if 'password' in user_data:
            user_data['password'] = make_password(user_data['password'])

        # Actualizar los datos del usuario
        user_serializer.save()

        # Extraer role_id antes de la serialización
        role_id = None
        if volunteer_data and 'role' in volunteer_data:
            role_id = volunteer_data.pop('role', None)

        # Serializar los datos del voluntario para actualizarlos (si hay datos)
        if volunteer_data:
            volunteer_serializer = VolunteerSerializer(volunteer, data=volunteer_data, partial=True)
            if not volunteer_serializer.is_valid():
                return Response(volunteer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            volunteer_serializer.save()
        else:
            # Si no hay datos de voluntario, inicializar el serializador con los datos actuales
            volunteer_serializer = VolunteerSerializer(volunteer)
        
        # Procesar el rol si se proporcionó
        if role_id is not None:
            try:
                # Asegurarse de que role_id sea un entero
                role_id = int(role_id)
                auth_role = AuthRole.objects.get(id=role_id)
                # Crea o actualiza el rol del usuario en AuthUserRoles
                AuthUserRoles.objects.update_or_create(user=user, defaults={'role': auth_role})
            except (ValueError, TypeError):
                return Response({"error": "El ID del rol debe ser un número entero válido."}, status=status.HTTP_400_BAD_REQUEST)
            except AuthRole.DoesNotExist:
                return Response({"error": f"El rol con id {role_id} no existe."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Si el rol es Profesor (2), se actualizan o crean las relaciones con cursos
        if role_id == 2:
            if course_ids:
                try:
                    # Limpiar las relaciones existentes
                    VolunteerClass.objects.filter(id_volunteer=volunteer).delete()
                    
                    # Crear nuevas relaciones
                    for course_id in course_ids:
                        try:
                            class_instance = Class.objects.get(id=course_id)
                            VolunteerClass.objects.create(id_class=class_instance, id_volunteer=volunteer)
                        except Class.DoesNotExist:
                            return Response(
                                {"error": f"Curso con ID {course_id} no existe."},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                except Exception as e:
                    return Response({"error": f"Error al actualizar los cursos: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Si es Admin u otro rol distinto de Profesor, se eliminan las relaciones con cursos
            try:
                VolunteerClass.objects.filter(id_volunteer=volunteer).delete()
            except Exception as e:
                return Response({"error": f"Error al eliminar las relaciones de curso: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Obtener el email actualizado para la respuesta
        updated_user = AuthUser.objects.get(id=user_id)
        
        return Response({
            'user': UserAuthSerializer(updated_user).data,
            'volunteer': volunteer_serializer.data 
        }, status=status.HTTP_200_OK)
        
    @action(detail=False, methods=['PATCH'], url_path='disable_volunteer')
    def disable_volunteer(self, request):
        # Obtener el ID del voluntario enviado por el frontend
        volunteer_id = request.data.get('volunteer_id')

        # Validar que el ID del voluntario esté presente
        if not volunteer_id:
            return Response({"error": "Se requiere el ID del voluntario."}, status=status.HTTP_400_BAD_REQUEST)

        # Intentar obtener el voluntario
        try:
            volunteer = Volunteers.objects.get(pk=volunteer_id)
        except Volunteers.DoesNotExist:
            return Response({"error": "El voluntario no existe."}, status=status.HTTP_404_NOT_FOUND)

        # Actualizar el status del voluntario
        volunteer.status = 0  # Cambia 'Inactivo' por el valor que represente la desactivación en tu sistema
        volunteer.save()

        return Response({"message": "El estado del voluntario ha sido actualizado a inactivo."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['PATCH'], url_path='enable_volunteer')
    def enable_volunteer(self, request):
        # Obtener el ID del voluntario enviado por el frontend
        volunteer_id = request.data.get('volunteer_id')

        # Validar que el ID del voluntario esté presente
        if not volunteer_id:
            return Response({"error": "Se requiere el ID del voluntario."}, status=status.HTTP_400_BAD_REQUEST)

        # Intentar obtener el voluntario
        try:
            volunteer = Volunteers.objects.get(pk=volunteer_id)
        except Volunteers.DoesNotExist:
            return Response({"error": "El voluntario no existe."}, status=status.HTTP_404_NOT_FOUND)

        # Actualizar el status del voluntario a activo
        volunteer.status = 1  # Cambia '1' por el valor que represente la activación en tu sistema
        volunteer.save()

        return Response({"message": "El voluntario ha sido activado correctamente."}, status=status.HTTP_200_OK)