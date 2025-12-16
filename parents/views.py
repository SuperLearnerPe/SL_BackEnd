from rest_framework import viewsets, status 
from rest_framework.response import Response 
from rest_framework.decorators import action 
from rest_framework.exceptions import NotFound
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from api.models import Parents 
from .serializers import ParentSerializer, ParentDetailsSerializer

class ParentsViewSet(viewsets.ViewSet): 
    
    @swagger_auto_schema(
        operation_description="Obtener lista de todos los padres",
        responses={200: ParentDetailsSerializer(many=True), 500: "Error interno"},
        tags=['👨‍👩‍👧‍👦 Gestión de Padres']
    )
    def list(self, request): 
        parents = Parents.objects.all().order_by('-id') 
        serializer = ParentDetailsSerializer(parents, many=True) 
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Crear un nuevo padre",
        request_body=ParentSerializer,
        responses={201: ParentDetailsSerializer, 400: "Datos inválidos"},
        tags=['👨‍👩‍👧‍👦 Gestión de Padres']
    )
    def create(self, request):
        serializer = ParentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parent = serializer.save()
        return Response(ParentDetailsSerializer(parent).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Obtener padre por ID",
        manual_parameters=[
            openapi.Parameter('parent_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True)
        ],
        responses={200: ParentDetailsSerializer, 400: "Parámetro requerido", 404: "No encontrado"},
        tags=['👨‍👩‍👧‍👦 Gestión de Padres']
    )
    def retrieve(self, request):
        parent_id = request.query_params.get("parent_id")
        if not parent_id:
            return Response(
                {"detail": "El parámetro 'parent_id' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            parent = Parents.objects.get(pk=parent_id)
        except Parents.DoesNotExist:
            raise NotFound(detail="Parent not found.", code=404)
        serializer = ParentDetailsSerializer(parent)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Actualizar información de un padre",
        manual_parameters=[
            openapi.Parameter('parent_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True)
        ],
        request_body=ParentSerializer,
        responses={200: ParentDetailsSerializer, 400: "Datos inválidos", 404: "No encontrado"},
        tags=['👨‍👩‍👧‍👦 Gestión de Padres']
    )
    def update(self, request):
        parent_id = request.query_params.get("parent_id")
        if not parent_id:
            return Response(
                {"detail": "El parámetro 'parent_id' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST
            ) 
        try:
            parent = Parents.objects.get(pk=parent_id)
        except Parents.DoesNotExist:
            raise NotFound(detail="Parent not found.", code=404)
        serializer = ParentSerializer(parent, data=request.data)
        serializer.is_valid(raise_exception=True)
        parent = serializer.save()
        return Response(ParentDetailsSerializer(parent).data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Activar/Desactivar un padre",
        manual_parameters=[
            openapi.Parameter('parent_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True)
        ],
        responses={200: "Estado cambiado", 400: "Parámetro requerido", 404: "No encontrado"},
        tags=['👨‍👩‍👧‍👦 Gestión de Padres']
    )
    @action(detail=False, methods=["PUT"], url_path="toggle-status")
    def toggle_parent_status(self, request):
        parent_id = request.query_params.get("parent_id")
        if not parent_id:
            return Response(
                {"detail": "El parámetro 'parent_id' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            parent = Parents.objects.get(pk=parent_id)
        except Parents.DoesNotExist:
            raise NotFound(detail="Parent not found.", code=404)

        if parent.status == 1:
            parent.status = 0
            message = "Padre desactivado."
        else:
            parent.status = 1
            message = "Padre activado."

        parent.save()
        return Response({"detail": message}, status=status.HTTP_200_OK)
