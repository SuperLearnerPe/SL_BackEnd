from rest_framework import serializers
from .models import AuthUser, Class , Students ,AttendanceStudent ,Session ,Volunteers, AuthUserRoles

class AttendanceUpdateSerializer(serializers.Serializer):
    
    id = serializers.IntegerField()  # El campo id del estudiante
    attendance = serializers.CharField()
    class Meta:
        model = AttendanceStudent
        fields = ['id', 'attendance']

class UserSerializer(serializers.ModelSerializer):
    all_permissions = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    
    class Meta:
        model = AuthUser
        fields = ['id', 'email', 'all_permissions', 'groups', 'role']

    def get_all_permissions(self, obj):
        return list(obj.get_all_permissions())

    def get_groups(self, obj):
        return list(obj.groups.values_list('name', flat=True))

    def get_role(self, obj):
        # Suponiendo que AuthUserRoles tiene una relación con AuthUser y AuthRole
        user_role = AuthUserRoles.objects.filter(user=obj).first()  # Obtener el primer rol (o ajusta según tu lógica)
        if user_role:
            return user_role.role.id  # Devuelve el ID del rol en lugar del nombre
        return None  # Devuelve None si no tiene rol
    
class GetCourses(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ["id","category","name","day","start_time","end_time","color","status","created_at","updated_at"]
        

        
class AttendanceStatusSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceStudent
        fields = ['status']

    def get_status(self, obj):
        return obj.status
    
class GetStudentsClass(serializers.ModelSerializer):
    attendance = serializers.SerializerMethodField()
    
    class Meta:
        model = Students
        fields = [
            'id',
            'name',
            'last_name',
            'nationality',
            'document_type',
            'document_id',
            'birthdate',
            'gender',
            'status',
            'created_at',
            'updated_at',
            'parent',
            'attendance'
        ]

    def get_attendance(self, obj):
            # Obtener el session_id del contexto
            session_id = self.context.get('session_id')
            if session_id:
                try:
                    # Buscar el registro de asistencia para el estudiante y sesión actual
                    attendanceV = AttendanceStudent.objects.get(id_student=obj.id, id_session=session_id)
                    return attendanceV.attendance
                except AttendanceStudent.DoesNotExist:
                    return 'UNKNOWN'  # Valor predeterminado si no se encuentra el registro
            return 'UNKNOWN'  # V
        
class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Students
        fields = ['id', 'name', 'last_name']
              
class CourseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Class
        fields = "__all__"

class AttendanceStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceStudent
        fields = ['id', 'status']
        extra_kwargs = {
            'status': {'choices': [('ONTIME', 'ONTIME'), ('LATE', 'LATE'), ('FAIL', 'FAIL')]}
        }
        
class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['id_session', 'id_class','num_session', 'date']
        
class StudentWithStatusSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Students
        fields = ['id', 'name', 'last_name', 'status']  # Incluye todos los campos que necesitas

    def get_status(self, student):
        class_id = self.context.get('class_id')
        if class_id is None:
            return 'UNKNOWN'
        try:
            # Obtén el estado del estudiante para la clase específica
            attendance_record = AttendanceStudent.objects.get(id_student=student.id, id_class=class_id)
            return attendance_record.status
        except AttendanceStudent.DoesNotExist:
            return 'UNKNOWN' 
        
class UserDataSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()  # Campo personalizado para el email

    class Meta:
        model = Volunteers
        fields = ['id', 'name', 'last_name', 'personal_email', 'photo', 'phone', 'user_id', 'email']

    def get_email(self, obj):
        # Accede al campo 'user' que es una ForeignKey al modelo auth_user
        return obj.user.email if obj.user else None