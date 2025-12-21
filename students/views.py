from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from api.models import Parents, BirthStudents  
from api.models import Students, Courses, StudentCourses
from .serializers import StudentSerializer, StudentDetailsSerializer, StudentPartialUpdateSerializer,StudentCourseInfoSerializer
from django.db.models import Prefetch
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class StudentsViewSet(viewsets.ViewSet):
    
    @swagger_auto_schema(
        operation_description="Obtener lista de todos los estudiantes",
        responses={200: StudentDetailsSerializer(many=True), 500: "Error interno"},
        tags=['🎓 Estudiantes']
    )
    # @action(detail=False, methods=["GET"], url_path="get")
    def list(self, request):
        students = Students.objects.all().order_by('-id').select_related('parent').prefetch_related(
            'course_enrollments__id_course',  
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
        tags=['🎓 Estudiantes']
    )
    # @action(detail=False, methods=["POST"], url_path="create")
    def create(self, request):
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
        tags=['🎓 Estudiantes']
    )
    # @action(detail=False, methods=["GET"], url_path="get-id")
    def retrieve(self, request):
        student_id = request.query_params.get("student_id")
        if not student_id:
            return Response(
                {"detail": "Debe enviar el parámetro student_id en la URL."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            student = Students.objects.filter(pk=student_id).select_related('parent').prefetch_related(
                'course_enrollments__id_course',  
                Prefetch('birthstudents_set', queryset=BirthStudents.objects.all(), to_attr='birth_prefetched')
            ).first()
            
            if not student:
                raise NotFound(detail="Estudiante no encontrado.", code=404)
                
            serializer = StudentDetailsSerializer(student)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Students.DoesNotExist:
            raise NotFound(detail="Estudiante no encontrado.", code=404)

    @swagger_auto_schema(
        operation_description="Actualizar información básica de un estudiante (parcial)",
        manual_parameters=[
            openapi.Parameter('student_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'gender': openapi.Schema(type=openapi.TYPE_STRING),
                'status': openapi.Schema(type=openapi.TYPE_INTEGER, description="0=Inactivo, 1=Activo")
            }
        ),
        responses={200: "Estudiante actualizado", 400: "Datos inválidos", 404: "No encontrado"},
        tags=['🎓 Estudiantes']
    )
    # @action(detail=False, methods=["PATCH"], url_path="update")
    def partial_update(self, request):
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

    def _assign_courses_logic(self, student, course_ids):
        """Lógica interna para asignar cursos a un estudiante"""
        # Obtener cursos existentes
        existing_courses = Courses.objects.filter(id__in=course_ids)
        existing_course_ids = set(existing_courses.values_list('id', flat=True))
        not_found_ids = [cid for cid in course_ids if cid not in existing_course_ids]

        # Verificar cursos ya asignados
        already_assigned = StudentCourses.objects.filter(
            id_student=student,
            id_course_id__in=existing_course_ids
        ).select_related('id_course')
        
        already_assigned_ids = set(sc.id_course.id for sc in already_assigned)
        
        # Cursos a asignar (existen y no están asignados)
        courses_to_assign = existing_courses.exclude(id__in=already_assigned_ids)

        # Asignar cursos en una transacción atómica
        assigned_courses = []
        try:
            with transaction.atomic():
                for course in courses_to_assign:
                    StudentCourses.objects.create(
                        id_student=student,
                        id_course=course
                    )
                    assigned_courses.append({
                        'id': course.id,
                        'name': course.name
                    })
        except Exception as e:
            return Response(
                {"detail": f"Error al asignar cursos: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Preparar respuesta
        response_data = {
            'message': f"Se procesaron {len(course_ids)} curso(s) para el estudiante {student.name} {student.last_name}.",
            'assigned': assigned_courses,
            'already_assigned': [
                {'id': sc.id_course.id, 'name': sc.id_course.name}
                for sc in already_assigned
            ],
            'not_found': not_found_ids
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def _remove_courses_logic(self, student, course_ids):
        """Lógica interna para remover cursos de un estudiante"""
        removed_courses = []
        for course_id in course_ids:
            StudentCourses.objects.filter(id_student=student, id_course_id=course_id).delete()
            try:
                course = Courses.objects.get(pk=course_id)
                removed_courses.append({'id': course.id, 'name': course.name})
            except Courses.DoesNotExist:
                pass

        return Response(
            {
                "message": "Cursos removidos con éxito",
                "removed_courses": removed_courses
            },
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        method='post',
        operation_description="Asignar cursos a un estudiante",
        manual_parameters=[
            openapi.Parameter('id', openapi.IN_PATH, type=openapi.TYPE_INTEGER, required=True, description="ID del estudiante")
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['course_ids'],
            properties={
                'course_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description="Lista de IDs de cursos a asignar"
                )
            }
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'assigned': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'name': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    ),
                    'already_assigned': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'name': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    ),
                    'not_found': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_INTEGER)
                    )
                }
            ),
            400: "Datos inválidos",
            404: "Estudiante no encontrado"
        },
        tags=['🎓 Estudiantes']
    )
    @swagger_auto_schema(
        method='delete',
        operation_description="Remover cursos de un estudiante",
        manual_parameters=[
            openapi.Parameter('id', openapi.IN_PATH, type=openapi.TYPE_INTEGER, required=True, description="ID del estudiante")
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['course_ids'],
            properties={
                'course_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description="Lista de IDs de cursos a remover"
                )
            }
        ),
        responses={200: "Cursos removidos", 400: "Datos inválidos", 404: "No encontrado"},
        tags=['🎓 Estudiantes']
    )
    @action(detail=True, methods=["POST", "DELETE"], url_path="courses")
    def manage_courses(self, request, pk=None):
        """
        Gestiona los cursos de un estudiante.
        POST: Asigna cursos a un estudiante.
        DELETE: Remueve cursos de un estudiante.
        """
        # Validar estudiante
        try:
            student = Students.objects.get(pk=pk)
        except Students.DoesNotExist:
            raise NotFound(detail="Estudiante no encontrado.", code=404)

        # Validar course_ids
        course_ids = request.data.get('course_ids', [])
        if not course_ids:
            return Response(
                {"detail": "Debe proporcionar al menos un ID de curso en 'course_ids'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(course_ids, list):
            return Response(
                {"detail": "'course_ids' debe ser una lista de IDs."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar que los IDs sean enteros (solo para POST)
        if request.method == "POST" and not all(isinstance(id, int) for id in course_ids):
            return Response(
                {"detail": "Todos los IDs de cursos deben ser enteros."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ejecutar la lógica correspondiente según el método
        if request.method == "POST":
            return self._assign_courses_logic(student, course_ids)
        elif request.method == "DELETE":
            return self._remove_courses_logic(student, course_ids)
