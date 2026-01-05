from rest_framework import serializers
from api.models import Volunteers, AuthUser, AuthUserRoles, VolunteerCourses
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class GetVolunteersSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    course_ids = serializers.SerializerMethodField()  # Nuevo campo para devolver la lista de IDs de cursos
    avatar_url = serializers.SerializerMethodField()  # URL del endpoint de avatar
    
    class Meta:
        model = Volunteers
        fields = ['id', 'name', 'last_name', 'email', 'personal_email', 'phone', 'photo', 'nationality', 'document_type', 'document_id', 'birthdate', 'gender', 'status', 'created_at', 'updated_at', 'user', 'role', 'course_ids', 'avatar_url', 'avatar_updated_at']
    
    def get_role(self, obj):
        try:
            # Primero obtenemos el objeto AuthUser
            auth_user = AuthUser.objects.get(id=obj.user_id)
            
            # Buscamos el rol directamente por user_id en lugar del objeto
            # Esto evita el error de tipos incompatibles
            user_role = AuthUserRoles.objects.filter(user_id=auth_user.id).first()
            
            if user_role:
                return user_role.role.id  # Devolver el ID del rol
            return None  # Devolver None si no se encuentra rol
            
        except Exception :
            # Silenciar la excepción para no mostrar errores en la consola
            return None  # En caso de error, devolver None

    def get_email(self, obj):
        auth_user = AuthUser.objects.filter(id=obj.user_id).first()
        if auth_user:
            return auth_user.email  # Devolver el email del usuario
        return None  # Devolver None si no se encuentra usuario

    def get_course_ids(self, obj):
        # Obtener todos los cursos asociados al voluntario desde VolunteerCourses
        volunteer_courses = VolunteerCourses.objects.filter(id_volunteer=obj.id)
        # Extraer los IDs de los cursos de las instancias de VolunteerCourses
        course_ids = volunteer_courses.values_list('id_course', flat=True)
        return list(course_ids)  # Devolver los IDs de los cursos como una lista
    
    def get_avatar_url(self, obj):
        """Genera la URL para obtener el avatar del voluntario"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(reverse('volunteers-get-avatar', kwargs={'pk': obj.pk}))
            return f'/volunteers/{obj.pk}/avatar'
        return None

    
class UserAuthSerializer(serializers.ModelSerializer):

    class Meta:
        model = AuthUser
        fields = ['username', 'email', 'password', 'first_name', 'last_name']
        
class VolunteerSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False, allow_null=True, write_only=True)
    
    class Meta:
        model = Volunteers
        fields = ['name', 'last_name', 'personal_email', 'photo', 'phone', 'nationality', 'document_type', 'document_id', 'birthdate', 'gender', 'status', 'user', 'avatar']
    
    def validate_avatar(self, value):
        """Validar el archivo de avatar"""
        if value:
            # Validar tipo de archivo
            allowed_types = ['image/jpeg', 'image/png', 'image/webp']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError(
                    f"Tipo de archivo no permitido. Solo se aceptan: {', '.join(allowed_types)}"
                )
            
            # Validar tamaño (1MB máximo)
            max_size = 1 * 1024 * 1024  # 1MB en bytes
            if value.size > max_size:
                raise serializers.ValidationError(
                    f"El archivo es demasiado grande. Tamaño máximo: 1MB. Tamaño actual: {value.size / (1024 * 1024):.2f}MB"
                )
        
        return value
    
    def create(self, validated_data):
        """Sobrescribir create para manejar el avatar"""
        avatar_file = validated_data.pop('avatar', None)
        volunteer = super().create(validated_data)
        
        if avatar_file:
            from django.utils import timezone
            volunteer.avatar = avatar_file.read()
            volunteer.avatar_content_type = avatar_file.content_type
            volunteer.avatar_updated_at = timezone.now()
            volunteer.save()
        
        return volunteer
    
    def update(self, instance, validated_data):
        """Sobrescribir update para manejar el avatar"""
        avatar_file = validated_data.pop('avatar', None)
        volunteer = super().update(instance, validated_data)
        
        if avatar_file:
            from django.utils import timezone
            volunteer.avatar = avatar_file.read()
            volunteer.avatar_content_type = avatar_file.content_type
            volunteer.avatar_updated_at = timezone.now()
            volunteer.save()
        
        return volunteer


