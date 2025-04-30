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
        operation_description="Genera un informe Excel completo con todas las métricas de impacto",
        manual_parameters=[
            openapi.Parameter('periodo', openapi.IN_QUERY, description="Periodo a analizar (semana, mes, año)", type=openapi.TYPE_STRING, default='mes'),
            openapi.Parameter('umbral_regular', openapi.IN_QUERY, description="Umbral de asistencia regular (0.0-1.0)", type=openapi.TYPE_NUMBER, default=0.5),
            openapi.Parameter('meses_retencion', openapi.IN_QUERY, description="Meses para análisis de retención", type=openapi.TYPE_INTEGER, default=6)
        ]
    )
    @action(detail=False, methods=["GET"], url_path="excel")
    def excel_impacto(self, request):
        periodo = request.query_params.get("periodo", "mes")
        umbral_regular = float(request.query_params.get("umbral_regular", 0.5))
        meses_retencion = int(request.query_params.get("meses_retencion", 6))
        
        excel_file = ExcelService.generar_excel_impacto(periodo, umbral_regular, meses_retencion)
        
        fecha_actual = datetime.now().strftime('%Y%m%d-%H%M%S')
        response = HttpResponse(
            excel_file,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=metricas_impacto_{fecha_actual}.xlsx'
        
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
        operation_description="Genera un informe Excel completo con todas las métricas de gestión",
        manual_parameters=[
            openapi.Parameter('fecha', openapi.IN_QUERY, description="Fecha para asistencia diaria (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('fecha_inicio', openapi.IN_QUERY, description="Fecha inicio para asistencia semanal (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('mes', openapi.IN_QUERY, description="Mes para asistencia mensual (1-12)", type=openapi.TYPE_INTEGER),
            openapi.Parameter('anio', openapi.IN_QUERY, description="Año para asistencia mensual", type=openapi.TYPE_INTEGER),
            openapi.Parameter('clase_id', openapi.IN_QUERY, description="ID de clase para filtrar", type=openapi.TYPE_INTEGER),
            openapi.Parameter('umbral_irregular', openapi.IN_QUERY, description="Umbral para asistencia irregular (0.0-1.0)", type=openapi.TYPE_NUMBER, default=0.25),
            openapi.Parameter('criterio', openapi.IN_QUERY, description="Criterio para análisis por grupos (sexo, edad)", type=openapi.TYPE_STRING, default='sexo'),
            openapi.Parameter('dias_inactivos', openapi.IN_QUERY, description="Días para considerar alumnos inactivos", type=openapi.TYPE_INTEGER, default=30)
        ]
    )
    @action(detail=False, methods=["GET"], url_path="excel")
    def excel_gestion(self, request):
        # Procesar parámetros
        fecha_str = request.query_params.get("fecha")
        fecha_inicio_str = request.query_params.get("fecha_inicio")
        mes = request.query_params.get("mes")
        anio = request.query_params.get("anio")
        clase_id = request.query_params.get("clase_id")
        umbral_irregular = float(request.query_params.get("umbral_irregular", 0.25))
        criterio = request.query_params.get("criterio", "sexo")
        dias_inactivos = int(request.query_params.get("dias_inactivos", 30))
        
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
        
        # Generar Excel
        excel_file = ExcelService.generar_excel_gestion(
            fecha, fecha_inicio, mes, anio, clase_id,
            umbral_irregular, criterio, dias_inactivos
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
        operation_description="Dashboard principal con resumen de métricas"
    )
    @action(detail=False, methods=["GET"], url_path="dashboard")
    def dashboard(self, request):
        # Recopilar métricas principales para el dashboard
        tasa_asistencia = ImpactoService.calcular_tasa_asistencia("mes")
        clases_asistencia = ImpactoService.asistencia_por_clase("mes")[:5]  # Top 5 clases
        alumnos_regulares = ImpactoService.alumnos_asistencia_regular("mes", 0.5)
        alumnos_irregulares = GestionService.alumnos_asistencia_irregular("mes", 0.25)
        dias_asistencia = ImpactoService.dia_mayor_asistencia("mes")
        
        # Obtener alumnos inactivos (más de 30 días)
        alumnos_inactivos = GestionService.alumnos_inactivos(30)
        
        # Construir respuesta para el dashboard
        dashboard_data = {
            "asistencia": {
                "tasa_mensual": tasa_asistencia.get("tasa_asistencia", 0),
                "total_asistencias": tasa_asistencia.get("total_asistencias", 0),
                "total_sesiones": tasa_asistencia.get("total_sesiones", 0)
            },
            "clases_destacadas": clases_asistencia,
            "alumnos": {
                "regulares": {
                    "porcentaje": alumnos_regulares.get("porcentaje_alumnos_regulares", 0),
                    "total": alumnos_regulares.get("total_alumnos_regulares", 0)
                },
                "irregulares": {
                    "porcentaje": alumnos_irregulares.get("porcentaje", 0),
                    "total": alumnos_irregulares.get("total_alumnos_irregulares", 0)
                },
                "inactivos": {
                    "total": alumnos_inactivos.get("total_alumnos_inactivos", 0)
                }
            },
            "dias_asistencia": dias_asistencia.get("asistencias_por_dia", {}),
            "dia_mayor_asistencia": dias_asistencia.get("dia_mayor_asistencia", "")
        }
        
        return Response(dashboard_data, status=status.HTTP_200_OK)