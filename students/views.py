from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from api.models import Parents, BirthStudents  
from api.models import Students, Class, StudentClass
from .serializers import StudentSerializer, StudentDetailsSerializer, StudentPartialUpdateSerializer,StudentCourseInfoSerializer
from django.db.models import Prefetch
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class StudentsViewSet(viewsets.ViewSet):
    
    @swagger_auto_schema(
        operation_description="Obtener lista de todos los estudiantes",
        responses={200: StudentDetailsSerializer(many=True), 500: "Error interno"},
        tags=['Students']
    )
    @action(detail=False, methods=["GET"], url_path="get")
    def list_students(self, request):
        students = Students.objects.all().order_by('-id').select_related('parent').prefetch_related(
            'studentclass_set__id_class',  
            Prefetch('birthstudents_set', queryset=BirthStudents.objects.all(), to_attr='birth_prefetched')
        )
        
        serializer = StudentDetailsSerializer(students, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Crear un nuevo estudiante",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'parent_dni': openapi.Schema(type=openapi.TYPE_STRING),
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'gender': openapi.Schema(type=openapi.TYPE_STRING),
                'birth_info': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'city': openapi.Schema(type=openapi.TYPE_STRING),
                        'country': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            }
        ),
        responses={201: "Estudiante creado", 400: "Datos inválidos"},
        tags=['Students']
    )
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
    
    @swagger_auto_schema(
        operation_description="Obtener estudiante por ID",
        manual_parameters=[
            openapi.Parameter('student_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True)
        ],
        responses={200: StudentDetailsSerializer(), 400: "Parámetro requerido", 404: "No encontrado"},
        tags=['Students']
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
                raise NotFound(detail="Estudiante no encontrado.", code=404)
                
            serializer = StudentDetailsSerializer(student)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Students.DoesNotExist:
            raise NotFound(detail="Estudiante no encontrado.", code=404)

    @swagger_auto_schema(
        operation_description="Actualizar información básica de un estudiante",
        manual_parameters=[
            openapi.Parameter('student_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'gender': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={200: "Estudiante actualizado", 400: "Datos inválidos", 404: "No encontrado"},
        tags=['Students']
    )
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

        serializer = StudentPartialUpdateSerializer(
            student,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"detail": "Información del estudiante actualizada correctamente."},
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_description="Activar/Desactivar un estudiante",
        manual_parameters=[
            openapi.Parameter('student_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True)
        ],
        responses={200: "Estado cambiado", 400: "Parámetro requerido", 404: "No encontrado"},
        tags=['Students']
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

        if student.status == 1:
            student.status = 0
            message = "Estudiante desactivado."
        else:
            student.status = 1
            message = "Estudiante activado."
        
        student.save()
        
        return Response({"detail": message}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Asignar cursos a un estudiante",
        manual_parameters=[
            openapi.Parameter('student_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'class_id': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description="Lista de IDs de cursos a asignar"
                )
            }
        ),
        responses={200: "Cursos asignados", 400: "Datos inválidos", 404: "No encontrado"},
        tags=['Students']
    )
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
                StudentClass.objects.get_or_create(id_student=student, id_class=course)
                assigned_courses.append(course.name)
            except Class.DoesNotExist:
                return Response({"detail": f"Curso con ID {course_id} no encontrado."}, status=404)

        return Response(
            {
                "message": "Cursos asignados con éxito",
                "assigned_courses": assigned_courses
            },
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_description="Remover cursos de un estudiante",
        manual_parameters=[
            openapi.Parameter('student_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'class_id': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description="Lista de IDs de cursos a remover"
                )
            }
        ),
        responses={200: "Cursos removidos", 400: "Datos inválidos", 404: "No encontrado"},
        tags=['Students']
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
            return Response({"detail": "class_id debe ser una lista de IDs de cursos."}, status=400)

        removed_courses = []
        for course_id in class_id:
            StudentClass.objects.filter(id_student=student, id_class=course_id).delete()
            try:
                course = Class.objects.get(pk=course_id)
                removed_courses.append(course.name)
            except Class.DoesNotExist:
                pass

        return Response(
            {
                "message": "Cursos removidos con éxito",
                "removed_courses": removed_courses
            },
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_description="Mover estudiante de unos cursos a otros",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'student_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'old_class_id': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER)
                ),
                'new_class_id': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER)
                )
            }
        ),
        responses={200: "Cursos movidos", 400: "Datos inválidos", 404: "No encontrado"},
        tags=['Students']
    )
    @action(detail=False, methods=["POST"], url_path="move-courses")
    def move_courses(self, request):
        student_id = request.data.get('student_id')
        if not student_id:
            return Response({"detail": "student_id es requerido"}, status=400)
        try:
            student = Students.objects.get(pk=student_id)
        except Students.DoesNotExist:
            raise NotFound(detail="Estudiante no encontrado.", code=404)

        old_class_id = request.data.get('old_class_id')
        new_class_id = request.data.get('new_class_id')

        if not isinstance(old_class_id, list) or not isinstance(new_class_id, list):
            return Response({"detail": "old_class_id y new_class_id deben ser listas"}, status=400)

        removed_courses = []
        for course_id in old_class_id:
            StudentClass.objects.filter(id_student=student, id_class=course_id).delete()
            try:
                course = Class.objects.get(pk=course_id)
                removed_courses.append(course.name)
            except Class.DoesNotExist:
                pass

        assigned_courses = []
        for course_id in new_class_id:
            try:
                course = Class.objects.get(pk=course_id)
                StudentClass.objects.get_or_create(id_student=student, id_class=course)
                assigned_courses.append(course.name)
            except Class.DoesNotExist:
                pass

        return Response(
            {
                "message": f"El estudiante {student.name} ha sido actualizado. Cursos removidos y asignados correctamente.",
                "removed_courses": removed_courses,
                "assigned_courses": assigned_courses
            },
            status=status.HTTP_200_OK
        )
    
    @swagger_auto_schema(
        operation_description="Obtener información de cursos de todos los estudiantes",
        responses={200: StudentCourseInfoSerializer(many=True), 500: "Error interno"},
        tags=['Students']
    )
    @action(detail=False, methods=["GET"], url_path="all-students-courses-info")
    def get_all_students_courses_info(self, request):
        students = Students.objects.all().prefetch_related(
            'studentclass_set__id_class'
        ).order_by('-id')
        
        serializer = StudentCourseInfoSerializer(students, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Obtener información de cursos de un estudiante específico",
        manual_parameters=[
            openapi.Parameter('student_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True)
        ],
        responses={200: StudentCourseInfoSerializer(), 400: "Parámetro requerido", 404: "No encontrado"},
        tags=['Students']
    )
    @action(detail=False, methods=["GET"], url_path="student-courses-info")
    def get_student_courses_info(self, request):
        student_id = request.query_params.get("student_id")
        if not student_id:
            return Response({"detail": "student_id es requerido"}, status=400)
        try:
            student = Students.objects.get(pk=student_id)
        except Students.DoesNotExist:
            raise NotFound(detail="Estudiante no encontrado.", code=404)

        serializer = StudentCourseInfoSerializer(student)
        return Response(serializer.data, status=status.HTTP_200_OK)