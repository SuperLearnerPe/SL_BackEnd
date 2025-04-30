from rest_framework import viewsets, status 
from rest_framework.response import Response 
from rest_framework.decorators import action 
from rest_framework.exceptions import NotFound

from api.models import Parents 
from .serializers import ParentSerializer, ParentDetailsSerializer

class ParentsViewSet(viewsets.ViewSet): 
    
    @action(detail=False, methods=["GET"], url_path="get") 
    def list_parents(self, request): 
        parents = Parents.objects.all().order_by('-id') 
        serializer = ParentDetailsSerializer(parents, many=True) 
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=["POST"], url_path="create")
    def create_parent(self, request):
        serializer = ParentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parent = serializer.save()
        return Response(ParentDetailsSerializer(parent).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["GET"], url_path="get-id")
    def retrieve_parent(self, request):
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

    @action(detail=False, methods=["PUT"], url_path="update")
    def update_parent(self, request):
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
