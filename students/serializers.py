from rest_framework import serializers


from api.models import Students ,Class

class StudentSerializer(serializers.ModelSerializer): 

    class Meta: 
        model = Students 
        fields = [ 'id', 'name', 'last_name', 'parent', 'nationality', 'document_type', 'document_id', 'birthdate','status', 'gender'] # Si deseas permitir q

class StudentDetailsSerializer(serializers.ModelSerializer): 
   
    parent_info = serializers.SerializerMethodField(read_only=True) 
    courses = serializers.SerializerMethodField(read_only=True)
    birth_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Students
        fields = [
            'id',
            'name',
            'last_name',
            'parent',
            'parent_info',
            'nationality',
            'document_type',
            'document_id',
            'birthdate',
            'gender',
            'status',
            'courses',
            'birth_info',
        ]

    def get_parent_info(self, obj):
        """
        Retorna datos del padre (Parents) asociado, si existe.
        """
        if obj.parent:
            return {
                "dni": obj.parent.document_id,
                "parent_name": obj.parent.name,
                "parent_last_name": obj.parent.last_name,
                "parent_email": obj.parent.email
            }
        return None

    def get_courses(self, obj):
        """
        Retorna la lista de cursos usando los datos prefetched
        """
        # Ya no necesita hacer consulta, usa los datos prefetch
        return [
            {
                "class_id": sc.id_class.id,
                "course_name": sc.id_class.name,
                "category": sc.id_class.category,
            }
            for sc in obj.studentclass_set.all()  # Usa los datos ya cargados
        ]
    
    def get_birth_info(self, obj):
        """
        Retorna la información de nacimiento usando datos prefetched
        """
        # Usa los datos precargados con Prefetch
        if hasattr(obj, 'birth_prefetched') and obj.birth_prefetched:
            birth = obj.birth_prefetched[0]
            return {
                "city": birth.city,
                "country": birth.country
            }
        return None

class StudentPartialUpdateSerializer(serializers.ModelSerializer):
    """Serializador para actualizar solo campos específicos de un estudiante"""
    
    class Meta:
        model = Students
        fields = ['name', 'last_name', 'gender', 'document_id', 'nationality', 'document_type','birthdate' , 'gender' , 'updated_at']


class CourseInfoSerializer(serializers.ModelSerializer):
    horario = serializers.SerializerMethodField()
    dia = serializers.CharField(source='day')

    class Meta:
        model = Class
        fields = ['id', 'name', 'horario', 'dia']

    def get_horario(self, obj):
        return f"{obj.start_time} - {obj.end_time}"

class StudentCourseInfoSerializer(serializers.ModelSerializer):
    courses_info = serializers.SerializerMethodField()

    class Meta:
        model = Students
        fields = ['id','name', 'last_name', 'document_id', 'courses_info']

    def get_courses_info(self, obj):

        return CourseInfoSerializer(
            [sc.id_class for sc in obj.studentclass_set.all()], 
            many=True
        ).data