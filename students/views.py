from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from api.models import Parents, BirthStudents  
from api.models import Students, Class, StudentClass
from .serializers import StudentSerializer, StudentDetailsSerializer, StudentPartialUpdateSerializer,StudentCourseInfoSerializer
from django.db.models import Prefetch

class StudentsViewSet(viewsets.ViewSet):
    
    
    @action(detail=False, methods=["GET"], url_path="get")
    def list_students(self, request):

        students = Students.objects.all().order_by('-id').select_related('parent').prefetch_related(
            'studentclass_set__id_class',  
            Prefetch('birthstudents_set', queryset=BirthStudents.objects.all(), to_attr='birth_prefetched')
        )
        
        # Sin paginación, todos los estudiantes a la vez
        serializer = StudentDetailsSerializer(students, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["POST"], url_path="create")
    def create_student(self, request):

        parent_dni = request.data.get("parent_dni")
        if not parent_dni:
            return Response(
                {"detail": "El campo 'parent_dni' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            parent = Parents.objects.get(document_id=parent_dni)
        except Parents.DoesNotExist:
            return Response(
                {"detail": "No existe un padre con el DNI proporcionado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        student_data = request.data.copy()
        student_data["parent"] = parent.id

        birth_info = student_data.get("birth_info")
        if not birth_info:
            return Response(
                {"detail": "El campo 'birth_info' es obligatorio y debe incluir 'city', 'state_department' y 'country'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not isinstance(birth_info, dict):
            return Response(
                {"detail": "'birth_info' debe ser un objeto JSON."},
                status=status.HTTP_400_BAD_REQUEST
            )

        student_data.pop("birth_info")

        serializer = StudentSerializer(data=student_data)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()

        BirthStudents.objects.create(
            id_student=student,
            city=birth_info.get("city"),
            country=birth_info.get("country")
        )

        return Response(
            StudentDetailsSerializer(student).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=["GET"], url_path="get-id")
    def retrieve_student(self, request):
        student_id = request.query_params.get("student_id")
        if not student_id:
            return Response(
                {"detail": "Debe enviar el parámetro student_id en la URL."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:

            student = Students.objects.filter(pk=student_id).select_related('parent').prefetch_related(
                'studentclass_set__id_class',  
                Prefetch('birthstudents_set', queryset=BirthStudents.objects.all(), to_attr='birth_prefetched')
            ).first()
            
            if not student:
                raise Students.DoesNotExist
                
            serializer = StudentDetailsSerializer(student)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Students.DoesNotExist:
            raise NotFound(detail="Estudiante no encontrado.", code=404)


    @action(detail=False, methods=["PUT"], url_path="update")
    def update_student_info(self, request):
        student_id = request.query_params.get("student_id")
        if not student_id:
            return Response(
                {"detail": "El parámetro 'student_id' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            student = Students.objects.get(pk=student_id)
        except Students.DoesNotExist:
            raise NotFound(detail="Estudiante no encontrado.", code=404)

        # Serializer para actualizar solo name, last_name y gender
        serializer = StudentPartialUpdateSerializer(
            student,
            data=request.data,
            partial=True  # Permite actualización parcial
        )

        # Validar y guardar los datos
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"detail": "Información del estudiante actualizada correctamente."},
            status=status.HTTP_200_OK
        )


    @action(detail=False, methods=["PUT"], url_path="toggle-status")
    def toggle_student_status(self, request):
        student_id = request.query_params.get("student_id")
        if not student_id:
            return Response(
                {"detail": "El parámetro 'student_id' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            student = Students.objects.get(pk=student_id)
        except Students.DoesNotExist:
            raise NotFound(detail="Estudiante no encontrado.", code=404)

        # Si el estudiante está activo (status 1) lo desactiva; de lo contrario, lo activa.
        if student.status == 1:
            student.status = 0
            message = "Estudiante desactivado."
        else:
            student.status = 1
            message = "Estudiante activado."
        
        # Guardar el cambio de estado directamente en la base de datos
        student.save()
        
        return Response({"detail": message}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["POST"], url_path="assign-courses")
    def assign_courses(self, request):
        student_id = request.query_params.get("student_id")
        if not student_id:
            return Response(
                {"detail": "El parámetro 'student_id' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            student = Students.objects.get(pk=student_id)
        except Students.DoesNotExist:
            raise NotFound(detail="Estudiante no encontrado.", code=404)

        class_id = request.data.get('class_id', [])
        if not isinstance(class_id, list):
            return Response(
                {"detail": "class_id debe ser una lista de IDs de cursos."},
                status=status.HTTP_400_BAD_REQUEST
            )

        assigned_courses = []
        for course_id in class_id:
            try:
                course = Class.objects.get(pk=course_id)
                # Crea la relación si no existe
                _, created = StudentClass.objects.get_or_create(
                    id_student=student,
                    id_class=course
                )
                if created:
                    assigned_courses.append(course.name or f"ID {course_id}")
            except Class.DoesNotExist:
                return Response(
                    {"error": f"El curso con ID {course_id} no existe."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(
            {
                "message": "Cursos asignados con éxito",
                "assigned_courses": assigned_courses
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["POST"], url_path="remove-courses")
    def remove_courses(self, request):
        student_id = request.query_params.get("student_id")
        if not student_id:
            return Response(
                {"detail": "El parámetro 'student_id' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            student = Students.objects.get(pk=student_id)
        except Students.DoesNotExist:
            raise NotFound(detail="Estudiante no encontrado.", code=404)

        class_id = request.data.get('class_id', [])
        if not isinstance(class_id, list):
            return Response(
                {"detail": "class_id debe ser una lista de IDs de cursos."},
                status=status.HTTP_400_BAD_REQUEST
            )

        removed_courses = []
        for course_id in class_id:
            try:
                course = Class.objects.get(pk=course_id)
            except Class.DoesNotExist:
                return Response(
                    {"error": f"El curso con ID {course_id} no existe."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Elimina la relación si existe
            deleted, _ = StudentClass.objects.filter(
                id_student=student, 
                id_class=course
            ).delete()
            if deleted:
                removed_courses.append(course.name or f"ID {course_id}")

        return Response(
            {
                "message": "Cursos removidos con éxito",
                "removed_courses": removed_courses
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["POST"], url_path="move-courses")
    def move_courses(self, request):
        student_id = request.data.get('student_id')
        if not student_id:
            return Response(
                {"detail": "El campo 'student_id' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            student = Students.objects.get(pk=student_id)
        except Students.DoesNotExist:
            raise NotFound(detail="Estudiante no encontrado.", code=404)

        old_class_id = request.data.get('old_class_id')
        new_class_id = request.data.get('new_class_id')

        if not isinstance(old_class_id, list) or not isinstance(new_class_id, list):
            return Response(
                {"detail": "'old_class_id' y 'new_class_id' deben ser listas de IDs de cursos."},
                status=status.HTTP_400_BAD_REQUEST
            )

        removed_courses = []
        for course_id in old_class_id:
            try:
                course = Class.objects.get(pk=course_id)
            except Class.DoesNotExist:
                return Response(
                    {"error": f"El curso con ID {course_id} no existe."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            deleted, _ = StudentClass.objects.filter(id_student=student, id_class=course).delete()
            if deleted:
                removed_courses.append(course.name or f"ID {course_id}")

        assigned_courses = []
        for course_id in new_class_id:
            try:
                course = Class.objects.get(pk=course_id)
            except Class.DoesNotExist:
                return Response(
                    {"error": f"El curso con ID {course_id} no existe."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            _, created = StudentClass.objects.get_or_create(
                id_student=student,
                id_class=course
            )
            if created:
                assigned_courses.append(course.name or f"ID {course_id}")

        return Response(
            {
                "message": (
                    f"El estudiante {student.name} ha sido actualizado. "
                    "Cursos removidos y asignados correctamente."
                ),
                "removed_courses": removed_courses,
                "assigned_courses": assigned_courses
            },
            status=status.HTTP_200_OK
        )
    

    @action(detail=False, methods=["GET"], url_path="all-students-courses-info")
    def get_all_students_courses_info(self, request):
        # Utiliza prefetch_related para cargar todas las relaciones StudentClass y Class de una vez
        students = Students.objects.all().prefetch_related(
            'studentclass_set__id_class'  # Carga clases en una sola consulta
        ).order_by('-id')
        
        serializer = StudentCourseInfoSerializer(students, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=["GET"], url_path="student-courses-info")
    def get_student_courses_info(self, request):
        student_id = request.query_params.get("student_id")
        if not student_id:
            return Response(
                {"detail": "El parámetro 'student_id' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            student = Students.objects.get(pk=student_id)
        except Students.DoesNotExist:
            raise NotFound(detail="Estudiante no encontrado.", code=404)

        serializer = StudentCourseInfoSerializer(student)
        return Response(serializer.data, status=status.HTTP_200_OK)