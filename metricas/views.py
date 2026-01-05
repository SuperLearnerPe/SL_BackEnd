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
            openapi.Parameter('periodo', openapi.IN_QUERY, type=openapi.TYPE_STRING, default='mes'),
            openapi.Parameter('clase_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER)
        ],
        tags=['📊 Métricas de Impacto']
    )    
    @action(detail=False, methods=["GET"], url_path="tasa-asistencia")
    def tasa_asistencia(self, request):
        periodo = request.query_params.get("periodo", "mes")
        clase_id = request.query_params.get("clase_id")
        
        if clase_id:
            try:
                clase_id = int(clase_id)
            except ValueError:
                return Response({"error": "clase_id debe ser un número entero"}, status=status.HTTP_400_BAD_REQUEST)
        
        datos = ImpactoService.calcular_tasa_asistencia(periodo, clase_id)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Tasas de asistencia por clase",
        manual_parameters=[
            openapi.Parameter('periodo', openapi.IN_QUERY, type=openapi.TYPE_STRING, default='mes')
        ],
        tags=['📊 Métricas de Impacto']
    )    
    @action(detail=False, methods=["GET"], url_path="asistencia-por-clase")
    def asistencia_por_clase(self, request):
        periodo = request.query_params.get("periodo", "mes")
        datos = ImpactoService.calcular_asistencia_por_clase(periodo)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Alumnos con asistencia regular",
        manual_parameters=[
            openapi.Parameter('periodo', openapi.IN_QUERY, type=openapi.TYPE_STRING, default='mes'),
            openapi.Parameter('umbral', openapi.IN_QUERY, type=openapi.TYPE_NUMBER, default=0.5)
        ],
        tags=['📊 Métricas de Impacto']
    )    
    @action(detail=False, methods=["GET"], url_path="alumnos-asistencia-regular")
    def alumnos_asistencia_regular(self, request):
        periodo = request.query_params.get("periodo", "mes")
        umbral = float(request.query_params.get("umbral", 0.5))
        datos = ImpactoService.calcular_alumnos_asistencia_regular(periodo, umbral)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Distribución de alumnos según número de asistencias",
        manual_parameters=[
            openapi.Parameter('periodo', openapi.IN_QUERY, type=openapi.TYPE_STRING, default='mes')
        ],
        tags=['📊 Métricas de Impacto']
    )    
    @action(detail=False, methods=["GET"], url_path="frecuencia-asistencia")
    def frecuencia_asistencia(self, request):
        periodo = request.query_params.get("periodo", "mes")
        datos = ImpactoService.calcular_frecuencia_asistencia(periodo)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Retención de alumnos mes a mes",
        manual_parameters=[
            openapi.Parameter('meses', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, default=6)
        ],
        tags=['📊 Métricas de Impacto']
    )    
    @action(detail=False, methods=["GET"], url_path="retencion-alumnos")
    def retencion_alumnos(self, request):
        periodo_meses = int(request.query_params.get("meses", 6))
        datos = ImpactoService.calcular_retencion_alumnos(periodo_meses)
        return Response(datos, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Días con mayor participación",
        manual_parameters=[
            openapi.Parameter('periodo', openapi.IN_QUERY, type=openapi.TYPE_STRING, default='mes')
        ],
        tags=['📊 Métricas de Impacto']
    )    
    @action(detail=False, methods=["GET"], url_path="dia-mayor-asistencia")
    def dia_mayor_asistencia(self, request):
        periodo = request.query_params.get("periodo", "mes")
        datos = ImpactoService.calcular_dia_mayor_asistencia(periodo)
        return Response(datos, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Promedio de sesiones por alumno",
        manual_parameters=[
            openapi.Parameter('periodo', openapi.IN_QUERY, type=openapi.TYPE_STRING, default='mes')
        ],
        tags=['📊 Métricas de Impacto']
    )    
    @action(detail=False, methods=["GET"], url_path="promedio-sesiones")
    def promedio_sesiones(self, request):
        periodo = request.query_params.get("periodo", "mes")
        datos = ImpactoService.promedio_sesiones(periodo)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Genera y descarga Excel con métricas de impacto",
        manual_parameters=[
            openapi.Parameter('periodo', openapi.IN_QUERY, type=openapi.TYPE_STRING, default='mes'),
            openapi.Parameter('umbral', openapi.IN_QUERY, type=openapi.TYPE_NUMBER, default=0.5)
        ],
        responses={
            200: openapi.Response(
                description="Archivo Excel generado",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        },
        tags=['📊 Métricas de Impacto - Excel']
    )
    @action(detail=False, methods=["GET"], url_path="excel")
    def excel_impacto(self, request):
        periodo = request.query_params.get("periodo", "mes")
        umbral = float(request.query_params.get("umbral", 0.5))
        
        try:
            excel_data = ExcelService.generar_excel_impacto(periodo, umbral)
            
            response = HttpResponse(
                excel_data,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="metricas_impacto_{periodo}_{datetime.now().strftime("%Y%m%d")}.xlsx"'
            return response
            
        except Exception as e:
            return Response(
                {"error": f"Error al generar el Excel: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
    
    @swagger_auto_schema(
        operation_description="Lista de asistencia diaria con nombre, sexo, edad",
        manual_parameters=[
            openapi.Parameter('fecha', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('clase_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER)
        ],
        tags=['📋 Gestión de Asistencia']
    )    
    @action(detail=False, methods=["GET"], url_path="asistencia-diaria")
    def asistencia_diaria(self, request):
        fecha = request.query_params.get("fecha")
        clase_id = request.query_params.get("clase_id")
        datos = GestionService.lista_asistencia_diaria(fecha, clase_id)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Lista de asistencia semanal con estadísticas",
        manual_parameters=[
            openapi.Parameter('fecha_inicio', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('clase_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER)
        ],
        tags=['📋 Gestión de Asistencia']
    )    
    @action(detail=False, methods=["GET"], url_path="asistencia-semanal")
    def asistencia_semanal(self, request):
        fecha_inicio = request.query_params.get("fecha_inicio")
        clase_id = request.query_params.get("clase_id")
        datos = GestionService.lista_asistencia_semanal(fecha_inicio, clase_id)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Lista de asistencia mensual con estadísticas",
        manual_parameters=[
            openapi.Parameter('mes', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('anio', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('clase_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER)
        ],
        tags=['📋 Gestión de Asistencia']
    )    
    @action(detail=False, methods=["GET"], url_path="asistencia-mensual")
    def asistencia_mensual(self, request):
        mes = request.query_params.get("mes")
        anio = request.query_params.get("anio")
        clase_id = request.query_params.get("clase_id")
        datos = GestionService.lista_asistencia_mensual(mes, anio, clase_id)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Alumnos con asistencia irregular",
        manual_parameters=[
            openapi.Parameter('periodo', openapi.IN_QUERY, type=openapi.TYPE_STRING, default='mes'),
            openapi.Parameter('umbral', openapi.IN_QUERY, type=openapi.TYPE_NUMBER, default=0.25)
        ],
        tags=['📋 Gestión de Asistencia']
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
            openapi.Parameter('criterio', openapi.IN_QUERY, type=openapi.TYPE_STRING, default='sexo'),
            openapi.Parameter('periodo', openapi.IN_QUERY, type=openapi.TYPE_STRING, default='mes')
        ],
        tags=['📋 Gestión de Asistencia']
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
            openapi.Parameter('dias', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, default=30)
        ],
        tags=['📋 Gestión de Asistencia']
    )
    @action(detail=False, methods=["GET"], url_path="alumnos-inactivos")
    def alumnos_inactivos(self, request):
        dias = int(request.query_params.get("dias", 30))
        datos = GestionService.alumnos_inactivos(dias)
        return Response(datos, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Genera y descarga informe Excel con métricas de gestión",
        manual_parameters=[
            openapi.Parameter('tipo', openapi.IN_QUERY, type=openapi.TYPE_STRING, default='completo', description="Tipo de reporte: diario, semanal, mensual, completo"),
            openapi.Parameter('fecha', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('fecha_inicio', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('mes', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('anio', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('clase_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER)
        ],
        responses={
            200: openapi.Response(
                description="Archivo Excel generado",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        },
        tags=['📋 Gestión de Asistencia - Excel']
    )    
    @action(detail=False, methods=["GET"], url_path="excel")
    def excel_gestion(self, request):
        # Extraer parámetros individuales
        tipo = request.query_params.get('tipo', 'completo')
        fecha = request.query_params.get('fecha')
        fecha_inicio = request.query_params.get('fecha_inicio')
        mes = request.query_params.get('mes')
        anio = request.query_params.get('anio')
        clase_id = request.query_params.get('clase_id')
        
        # Convertir fecha_inicio a objeto date si se proporciona
        fecha_inicio_obj = None
        if fecha_inicio:
            try:
                fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {"error": "Formato de fecha_inicio inválido. Use YYYY-MM-DD"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Convertir mes y anio a enteros si se proporcionan
        mes_int = None
        anio_int = None
        if mes:
            try:
                mes_int = int(mes)
            except ValueError:
                return Response(
                    {"error": "El mes debe ser un número entero entre 1 y 12"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if anio:
            try:
                anio_int = int(anio)
            except ValueError:
                return Response(
                    {"error": "El año debe ser un número entero"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Convertir clase_id a entero si se proporciona
        clase_id_int = None
        if clase_id:
            try:
                clase_id_int = int(clase_id)
            except ValueError:
                return Response(
                    {"error": "El clase_id debe ser un número entero"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            # Llamar al servicio con parámetros individuales
            excel_data = ExcelService.generar_excel_gestion(
                fecha=fecha,
                fecha_inicio=fecha_inicio_obj,
                mes=mes_int,
                anio=anio_int,
                clase_id=clase_id_int
            )
            
            response = HttpResponse(
                excel_data,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="gestion_asistencia_{tipo}_{datetime.now().strftime("%Y%m%d")}.xlsx"'
            return response
            
        except Exception as e:
            return Response(
                {"error": f"Error al generar el Excel: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MetricasViewSet(viewsets.ViewSet):
    
    @swagger_auto_schema(
        operation_description="Obtener métricas del sistema",
        responses={200: "Métricas obtenidas", 500: "Error interno"},
        tags=['📈 Métricas Generales']
    )
    @action(detail=False, methods=['GET'], url_path='get_metrics')
    def get_metrics(self, request):
        try:
            # Aquí implementarías la lógica para obtener métricas generales
            return Response({"message": "Endpoint en desarrollo"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        operation_description="Obtener estadísticas de usuarios",
        responses={200: "Estadísticas obtenidas", 500: "Error interno"},
        tags=['📈 Métricas Generales']
    )
    @action(detail=False, methods=['GET'], url_path='user_stats')
    def user_stats(self, request):
        try:
            # Aquí implementarías la lógica para obtener estadísticas de usuarios
            return Response({"message": "Endpoint en desarrollo"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)