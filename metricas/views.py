from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.http import HttpResponse
from .services.impacto_service import ImpactoService
from .services.gestion_service import GestionService
from .services.excel_service import ExcelService
from datetime import datetime
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class ImpactoViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        operation_description="Calcula la tasa de asistencia para un periodo",
        manual_parameters=[
            openapi.Parameter('periodo', openapi.IN_QUERY, description="Periodo a analizar (semana, mes, año)", type=openapi.TYPE_STRING, default='mes'),
            openapi.Parameter('clase_id', openapi.IN_QUERY, description="ID de la clase (opcional)", type=openapi.TYPE_INTEGER)
        ]
    )
    @action(detail=False, methods=["GET"], url_path="tasa-asistencia")
    def tasa_asistencia(self, request):
        periodo = request.query_params.get("periodo", "mes")
        clase_id = request.query_params.get("clase_id")
        
        if clase_id:
            try:
                clase_id = int(clase_id)
            except ValueError:
                return Response(
                    {"error": "El ID de clase debe ser un número entero"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        datos = ImpactoService.calcular_tasa_asistencia(periodo, clase_id)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Obtiene las tasas de asistencia desglosadas por clase",
        manual_parameters=[
            openapi.Parameter('periodo', openapi.IN_QUERY, description="Periodo a analizar (semana, mes, año)", type=openapi.TYPE_STRING, default='mes')
        ]
    )
    @action(detail=False, methods=["GET"], url_path="asistencia-por-clase")
    def asistencia_por_clase(self, request):
        periodo = request.query_params.get("periodo", "mes")
        datos = ImpactoService.asistencia_por_clase(periodo)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Lista los alumnos con asistencia regular",
        manual_parameters=[
            openapi.Parameter('periodo', openapi.IN_QUERY, description="Periodo a analizar (semana, mes, año)", type=openapi.TYPE_STRING, default='mes'),
            openapi.Parameter('umbral', openapi.IN_QUERY, description="Umbral de asistencia regular (0.0-1.0)", type=openapi.TYPE_NUMBER, default=0.5)
        ]
    )
    @action(detail=False, methods=["GET"], url_path="alumnos-asistencia-regular")
    def alumnos_asistencia_regular(self, request):
        periodo = request.query_params.get("periodo", "mes")
        umbral = float(request.query_params.get("umbral", 0.5))
        datos = ImpactoService.alumnos_asistencia_regular(periodo, umbral)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Distribución de alumnos según número de asistencias",
        manual_parameters=[
            openapi.Parameter('periodo', openapi.IN_QUERY, description="Periodo a analizar (semana, mes, año)", type=openapi.TYPE_STRING, default='mes')
        ]
    )
    @action(detail=False, methods=["GET"], url_path="frecuencia-asistencia")
    def frecuencia_asistencia(self, request):
        periodo = request.query_params.get("periodo", "mes")
        datos = ImpactoService.frecuencia_asistencia(periodo)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Número de alumnos que continúan asistiendo mes a mes",
        manual_parameters=[
            openapi.Parameter('meses', openapi.IN_QUERY, description="Número de meses a analizar", type=openapi.TYPE_INTEGER, default=6)
        ]
    )
    @action(detail=False, methods=["GET"], url_path="retencion-alumnos")
    def retencion_alumnos(self, request):
        periodo_meses = int(request.query_params.get("meses", 6))
        datos = ImpactoService.retencion_alumnos(periodo_meses)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Identifica qué días hay mayor o menor participación",
        manual_parameters=[
            openapi.Parameter('periodo', openapi.IN_QUERY, description="Periodo a analizar (semana, mes, año)", type=openapi.TYPE_STRING, default='mes')
        ]
    )
    @action(detail=False, methods=["GET"], url_path="dia-mayor-asistencia")
    def dia_mayor_asistencia(self, request):
        periodo = request.query_params.get("periodo", "mes")
        datos = ImpactoService.dia_mayor_asistencia(periodo)
        return Response(datos, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Promedio de sesiones asistidas por alumno",
        manual_parameters=[
            openapi.Parameter('periodo', openapi.IN_QUERY, description="Periodo a analizar (semana, mes, año)", type=openapi.TYPE_STRING, default='mes')
        ]
    )
    @action(detail=False, methods=["GET"], url_path="promedio-sesiones")
    def promedio_sesiones(self, request):
        periodo = request.query_params.get("periodo", "mes")
        datos = ImpactoService.promedio_sesiones(periodo)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="""
        Genera informe Excel con MÉTRICAS DE IMPACTO según requerimientos:
        
        ✅ Tasa de asistencia por clase/día y general
        ✅ Porcentaje de alumnos regulares (≥50%)
        ✅ Frecuencia de asistencia (1-3, 4-5, 6+)
        ✅ Retención mes a mes 
        ✅ Día con mayor asistencia
        ✅ Promedio de sesiones por alumno
        """,
        manual_parameters=[
            openapi.Parameter('periodo', openapi.IN_QUERY, description="[OPCIONAL] Periodo (semana, mes, año)", type=openapi.TYPE_STRING, default='mes', required=False),
        ]
    )
    @action(detail=False, methods=["GET"], url_path="excel")
    def excel_impacto(self, request):
        periodo = request.query_params.get("periodo", "mes")
        excel_file = ExcelService.generar_excel_impacto(periodo)
        
        response = HttpResponse(
            excel_file,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=SuperLearner_Metricas_Impacto.xlsx'
        
        return response

class GestionViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        operation_description="Lista de asistencia diaria con nombre, sexo, edad",
        manual_parameters=[
            openapi.Parameter('fecha', openapi.IN_QUERY, description="Fecha a consultar (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('clase_id', openapi.IN_QUERY, description="ID de la clase (opcional)", type=openapi.TYPE_INTEGER)
        ]
    )
    @action(detail=False, methods=["GET"], url_path="asistencia-diaria")
    def asistencia_diaria(self, request):
        fecha_str = request.query_params.get("fecha")
        clase_id = request.query_params.get("clase_id")
        
        fecha = None
        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Formato de fecha incorrecto. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        if clase_id:
            try:
                clase_id = int(clase_id)
            except ValueError:
                return Response(
                    {"error": "El ID de clase debe ser un número entero"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        datos = GestionService.lista_asistencia_diaria(fecha, clase_id)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Lista de asistencia semanal con estadísticas",
        manual_parameters=[
            openapi.Parameter('fecha_inicio', openapi.IN_QUERY, description="Fecha de inicio de semana (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('clase_id', openapi.IN_QUERY, description="ID de la clase (opcional)", type=openapi.TYPE_INTEGER)
        ]
    )
    @action(detail=False, methods=["GET"], url_path="asistencia-semanal")
    def asistencia_semanal(self, request):
        fecha_str = request.query_params.get("fecha_inicio")
        clase_id = request.query_params.get("clase_id")
        
        fecha_inicio = None
        if fecha_str:
            try:
                fecha_inicio = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Formato de fecha incorrecto. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        if clase_id:
            try:
                clase_id = int(clase_id)
            except ValueError:
                return Response(
                    {"error": "El ID de clase debe ser un número entero"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        datos = GestionService.lista_asistencia_semanal(fecha_inicio, clase_id)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Lista de asistencia mensual con estadísticas",
        manual_parameters=[
            openapi.Parameter('mes', openapi.IN_QUERY, description="Número del mes (1-12)", type=openapi.TYPE_INTEGER),
            openapi.Parameter('anio', openapi.IN_QUERY, description="Año", type=openapi.TYPE_INTEGER),
            openapi.Parameter('clase_id', openapi.IN_QUERY, description="ID de la clase (opcional)", type=openapi.TYPE_INTEGER)
        ]
    )
    @action(detail=False, methods=["GET"], url_path="asistencia-mensual")
    def asistencia_mensual(self, request):
        mes = request.query_params.get("mes")
        anio = request.query_params.get("anio")
        clase_id = request.query_params.get("clase_id")
        
        try:
            if mes:
                mes = int(mes)
            if anio:
                anio = int(anio)
            if clase_id:
                clase_id = int(clase_id)
        except ValueError:
            return Response(
                {"error": "Los parámetros mes, año y clase_id deben ser valores numéricos"},
                status=status.HTTP_400_BAD_REQUEST
            )
                
        datos = GestionService.lista_asistencia_mensual(mes, anio, clase_id)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Alumnos con asistencia irregular",
        manual_parameters=[
            openapi.Parameter('periodo', openapi.IN_QUERY, description="Periodo a analizar (semana, mes, año)", type=openapi.TYPE_STRING, default='mes'),
            openapi.Parameter('umbral', openapi.IN_QUERY, description="Umbral de asistencia irregular (0.0-1.0)", type=openapi.TYPE_NUMBER, default=0.25)
        ]
    )
    @action(detail=False, methods=["GET"], url_path="asistencia-irregular")
    def asistencia_irregular(self, request):
        periodo = request.query_params.get("periodo", "mes")
        umbral = float(request.query_params.get("umbral", 0.25))
        datos = GestionService.alumnos_asistencia_irregular(periodo, umbral)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Analiza asistencia por grupos",
        manual_parameters=[
            openapi.Parameter('criterio', openapi.IN_QUERY, description="Criterio de agrupación (sexo, edad)", type=openapi.TYPE_STRING, default='sexo'),
            openapi.Parameter('periodo', openapi.IN_QUERY, description="Periodo a analizar (semana, mes, año)", type=openapi.TYPE_STRING, default='mes')
        ]
    )
    @action(detail=False, methods=["GET"], url_path="grupos-asistencia")
    def grupos_asistencia(self, request):
        criterio = request.query_params.get("criterio", "sexo")
        periodo = request.query_params.get("periodo", "mes")
        datos = GestionService.analisis_grupos_asistencia(criterio, periodo)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Alumnos que faltaron más días consecutivos del umbral",
        manual_parameters=[
            openapi.Parameter('dias', openapi.IN_QUERY, description="Número mínimo de días de inactividad", type=openapi.TYPE_INTEGER, default=30)
        ]
    )
    @action(detail=False, methods=["GET"], url_path="alumnos-inactivos")
    def alumnos_inactivos(self, request):
        dias = int(request.query_params.get("dias", 30))
        datos = GestionService.alumnos_inactivos(dias)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="""
        Genera informe Excel con MÉTRICAS DE GESTIÓN según requerimientos:
        
        ✅ Lista diaria: nombre, sexo, edad
        ✅ Lista semanal: nombre, sexo, edad, total asistencias, porcentaje, estatus
        ✅ Lista mensual: nombre, sexo, edad, total asistencias, porcentaje, estatus
        ✅ Alumnos irregulares: <25% asistencia (FIJO)
        ✅ Grupos por sexo/edad
        ✅ Alumnos con más de 30 faltas seguidas (FIJO)
        """,
        manual_parameters=[
            openapi.Parameter('fecha', openapi.IN_QUERY, description="[OPCIONAL] Fecha específica (YYYY-MM-DD)", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('fecha_inicio', openapi.IN_QUERY, description="[OPCIONAL] Fecha inicio semana (YYYY-MM-DD)", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('mes', openapi.IN_QUERY, description="[OPCIONAL] Mes (1-12)", type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('anio', openapi.IN_QUERY, description="[OPCIONAL] Año", type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('clase_id', openapi.IN_QUERY, description="[OPCIONAL] ID de clase", type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('criterio', openapi.IN_QUERY, description="[OPCIONAL] Criterio grupos (sexo, edad)", type=openapi.TYPE_STRING, default='sexo', required=False),
        ]
    )
    @action(detail=False, methods=["GET"], url_path="excel")
    def excel_gestion(self, request):
        fecha_str = request.query_params.get("fecha")
        fecha_inicio_str = request.query_params.get("fecha_inicio")
        mes = request.query_params.get("mes")
        anio = request.query_params.get("anio")
        clase_id = request.query_params.get("clase_id")
        criterio = request.query_params.get("criterio", "sexo")
        
        # Convertir fechas si existen
        fecha = None
        fecha_inicio = None
        
        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Formato de fecha incorrecto. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if fecha_inicio_str:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Formato de fecha incorrecto. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Convertir parámetros numéricos
        if mes:
            mes = int(mes)
        if anio:
            anio = int(anio)
        if clase_id:
            clase_id = int(clase_id)
        
        # Generar Excel con valores fijos según requerimientos
        excel_file = ExcelService.generar_excel_gestion(
            fecha, fecha_inicio, mes, anio, clase_id,
            0.25,  # Umbral irregular fijo <25%
            criterio, 
            30     # Faltas seguidas fijo >30
        )
        
        fecha_actual = datetime.now().strftime('%Y%m%d-%H%M%S')
        response = HttpResponse(
            excel_file,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=metricas_gestion_{fecha_actual}.xlsx'
        
        return response

class MetricasViewSet(viewsets.ViewSet):
    
    @swagger_auto_schema(
        operation_description="Obtener métricas del sistema",
        responses={
            200: openapi.Response(
                description="Métricas obtenidas exitosamente"
            ),
            500: openapi.Response(description="Error interno del servidor")
        },
        tags=['Metricas']
    )
    @action(detail=False, methods=['GET'], url_path='get_metrics')
    def get_metrics(self, request):
        """Obtener métricas del sistema"""
        try:
            # Your implementation here
            return Response({"message": "Métricas del sistema"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        operation_description="Obtener estadísticas de usuarios",
        responses={
            200: openapi.Response(
                description="Estadísticas obtenidas exitosamente"
            ),
            500: openapi.Response(description="Error interno del servidor")
        },
        tags=['Metricas']
    )
    @action(detail=False, methods=['GET'], url_path='user_stats')
    def user_stats(self, request):
        """Obtener estadísticas de usuarios"""
        try:
            # Your implementation here
            return Response({"message": "Estadísticas de usuarios"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)