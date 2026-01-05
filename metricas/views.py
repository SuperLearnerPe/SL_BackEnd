from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.http import HttpResponse
from .services.excel_service import ExcelService
from datetime import datetime
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class GestionViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        operation_description="Descarga Excel de entidades (padres, estudiantes, voluntarios, cursos) filtrado por fecha de registro",
        manual_parameters=[
            openapi.Parameter('tipo_reporte', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True, description="Tipo de entidad: padres | estudiantes | voluntarios | cursos"),
            openapi.Parameter('fecha_inicio', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True, description="Fecha de inicio (YYYY-MM-DD)"),
            openapi.Parameter('fecha_fin', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True, description="Fecha de fin (YYYY-MM-DD)")
        ],
        responses={
            200: openapi.Response(
                description="Archivo Excel generado",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            400: "Parámetros inválidos",
            500: "Error al generar el archivo"
        },
        tags=['📋 Gestión de Asistencia - Excel']
    )
    @action(detail=False, methods=["GET"], url_path="excel-entidades")
    def excel_entidades(self, request):
        tipo_reporte = request.query_params.get('tipo_reporte')
        fecha_inicio_str = request.query_params.get('fecha_inicio')
        fecha_fin_str = request.query_params.get('fecha_fin')
        
        # Validar que al menos tipo_reporte sea obligatorio
        if not tipo_reporte:
            return Response(
                {"error": "Se requiere el parámetro: tipo_reporte"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar tipo de reporte
        tipos_validos = ['padres', 'estudiantes', 'voluntarios', 'cursos']
        if tipo_reporte not in tipos_validos:
            return Response(
                {"error": f"Tipo de reporte inválido. Debe ser uno de: {', '.join(tipos_validos)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar y convertir fechas (opcionales)
        fecha_inicio = None
        fecha_fin = None
        
        if fecha_inicio_str:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {"error": "Formato de fecha_inicio inválido. Use YYYY-MM-DD"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if fecha_fin_str:
            try:
                fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {"error": "Formato de fecha_fin inválido. Use YYYY-MM-DD"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validar que fecha_inicio sea menor que fecha_fin (si ambas están presentes)
        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            return Response(
                {"error": "La fecha de inicio debe ser anterior a la fecha de fin"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Generar el Excel según el tipo de reporte
            excel_data = ExcelService.generar_excel_entidades(
                tipo_reporte=tipo_reporte,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )
            
            # Preparar la respuesta
            response = HttpResponse(
                excel_data,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            # Generar nombre de archivo dinámico según filtros aplicados
            if fecha_inicio and fecha_fin:
                filename = f"reporte_{tipo_reporte}_{fecha_inicio_str}_a_{fecha_fin_str}.xlsx"
            elif fecha_inicio:
                filename = f"reporte_{tipo_reporte}_desde_{fecha_inicio_str}.xlsx"
            elif fecha_fin:
                filename = f"reporte_{tipo_reporte}_hasta_{fecha_fin_str}.xlsx"
            else:
                filename = f"reporte_{tipo_reporte}_completo.xlsx"
                
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            return Response(
                {"error": f"Error al generar el Excel: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )