from rest_framework import serializers
from api.models import Volunteers , AuthUser , AuthUserRoles, VolunteerClass

class GetVolunteersSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    course_ids = serializers.SerializerMethodField()  # Nuevo campo para devolver la lista de IDs de cursos
    
    class Meta:
        model = Volunteers
        fields = ['id', 'name', 'last_name', 'email', 'personal_email', 'phone', 'photo', 'nationality', 'document_type', 'document_id', 'birthdate', 'gender', 'status', 'created_at', 'updated_at', 'user', 'role', 'course_ids']  # Incluimos 'courses' en los campos
    
    def get_role(self, obj):
        # Obtener la instancia correspondiente de AuthUser a través de user_id en Volunteers
        auth_user = AuthUser.objects.get(id=obj.user_id)
        # Consultar el modelo AuthUserRoles usando el user (auth_user)
        user_role = AuthUserRoles.objects.filter(user=auth_user.id).first()
        if user_role:
            return user_role.role.id  # Devolver el ID del rol
        return None  # Devolver None si no se encuentra rol

    def get_email(self, obj):
        auth_user = AuthUser.objects.filter(id=obj.user_id).first()
        if auth_user:
            return auth_user.email  # Devolver el email del usuario
        return None  # Devolver None si no se encuentra usuario

    def get_course_ids(self, obj):
        # Obtener todos los cursos asociados al voluntario desde VolunteerClass
        volunteer_classes = VolunteerClass.objects.filter(id_volunteer=obj.id)
        # Extraer los IDs de los cursos de las instancias de VolunteerClass
        course_ids = volunteer_classes.values_list('id_class', flat=True)
        return list(course_ids)  # Devolver los IDs de los cursos como una lista

    
class UserAuthSerializer(serializers.ModelSerializer):

    class Meta:
        model = AuthUser
        fields = ['username', 'email', 'password', 'first_name', 'last_name']
        
class VolunteerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Volunteers
        fields = ['name', 'last_name', 'personal_email', 'photo', 'phone', 'nationality', 'document_type', 'document_id', 'birthdate', 'gender', 'status', 'user']

        