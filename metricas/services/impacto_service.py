from django.db.models import Count, Q
from datetime import datetime, timedelta
from api.models import AttendanceStudent, Session, Class

class ImpactoService:
    """Servicio para cálculo de métricas de impacto"""
    @staticmethod
    def calcular_tasa_asistencia(periodo, clase_id=None):
        """
        Calcula la tasa de asistencia según el periodo y opcionalmente para una clase específica
        """
        now = datetime.now().date()
        
        if periodo == 'semana':
            start_date = now - timedelta(days=now.weekday())
        elif periodo == 'mes':
            start_date = datetime(now.year, now.month, 1).date()
        elif periodo == 'año' or periodo == 'anio':
            start_date = datetime(now.year, 1, 1).date()
        else:
            start_date = now - timedelta(days=30)  # Default: último mes
            
        # Base query con filtro de fecha
        sessions_query = Session.objects.filter(date__gte=start_date)
        attendance_query = AttendanceStudent.objects.filter(id_session__date__gte=start_date)
        
        # Filtrar por clase si se especifica
        if clase_id:
            sessions_query = sessions_query.filter(id_class=clase_id)
            attendance_query = attendance_query.filter(id_session__id_class=clase_id)
        
        # Contar sesiones y asistencias con optimización
        total_sesiones = sessions_query.count()
        total_asistencias = attendance_query.filter(attendance__in=['ONTIME', 'LATE']).count()
        
        # Calcular estudiantes únicos solo una vez
        estudiantes_unicos = attendance_query.values('id_student').distinct().count()
        
        # Calcular tasa
        if total_sesiones > 0 and estudiantes_unicos > 0:
            asistencias_esperadas = total_sesiones * estudiantes_unicos
            tasa_asistencia = (total_asistencias / asistencias_esperadas) * 100
        else:
            tasa_asistencia = 0
            
        return {
            'tasa_asistencia': round(tasa_asistencia, 2),
            'total_sesiones': total_sesiones,
            'total_asistencias': total_asistencias,
            'estudiantes_unicos': estudiantes_unicos,
            'periodo': periodo
        }
    
    @staticmethod
    def calcular_asistencia_por_clase(periodo):
        """Calcula tasas de asistencia por clase"""
        clases = Class.objects.all()
        resultados = []
        
        for clase in clases:
            data = ImpactoService.calcular_tasa_asistencia(periodo, clase.id)
            resultados.append({
                'clase_id': clase.id,
                'clase_nombre': clase.name,
                'tasa_asistencia': data['tasa_asistencia'],
                'total_sesiones': data['total_sesiones'],
                'total_asistencias': data['total_asistencias'],
                'estudiantes_unicos': data['estudiantes_unicos']
            })
        
        return resultados
    
    @staticmethod
    def calcular_alumnos_asistencia_regular(periodo, umbral=0.5):
        """Calcula alumnos con asistencia regular"""
        now = datetime.now().date()
        
        if periodo == 'semana':
            start_date = now - timedelta(days=now.weekday())
        elif periodo == 'mes':
            start_date = datetime(now.year, now.month, 1).date()
        elif periodo == 'año' or periodo == 'anio':
            start_date = datetime(now.year, 1, 1).date()
        else:
            start_date = now - timedelta(days=30)
        
        # Obtener asistencias por estudiante
        attendance_data = AttendanceStudent.objects.filter(
            id_session__date__gte=start_date
        ).values(
            'id_student__id', 
            'id_student__name', 
            'id_student__last_name'
        ).annotate(
            total_asistencias=Count('id', filter=Q(attendance__in=['ONTIME', 'LATE'])),
            total_registros=Count('id')
        )
        
        alumnos_regulares = []
        for data in attendance_data:
            if data['total_registros'] > 0:
                tasa = data['total_asistencias'] / data['total_registros']
                if tasa >= umbral:
                    alumnos_regulares.append({
                        'estudiante_id': data['id_student__id'],
                        'nombre': f"{data['id_student__name']} {data['id_student__last_name']}",
                        'asistencias': data['total_asistencias'],
                        'total_sesiones': data['total_registros'],
                        'tasa_asistencia': round(tasa * 100, 2)
                    })
        
        return {
            'alumnos_regulares': alumnos_regulares,
            'total_alumnos_regulares': len(alumnos_regulares),
            'umbral_usado': umbral * 100
        }
    
    @staticmethod
    def calcular_frecuencia_asistencia(periodo):
        """Calcula distribución de alumnos según número de asistencias"""
        now = datetime.now().date()
        
        if periodo == 'semana':
            start_date = now - timedelta(days=now.weekday())
        elif periodo == 'mes':
            start_date = datetime(now.year, now.month, 1).date()
        elif periodo == 'año' or periodo == 'anio':
            start_date = datetime(now.year, 1, 1).date()
        else:
            start_date = now - timedelta(days=30)
        
        # Contar asistencias por estudiante
        frecuencias = AttendanceStudent.objects.filter(
            id_session__date__gte=start_date,
            attendance__in=['ONTIME', 'LATE']
        ).values('id_student').annotate(
            num_asistencias=Count('id')
        ).values('num_asistencias').annotate(
            num_estudiantes=Count('id_student')
        ).order_by('num_asistencias')
        
        return list(frecuencias)
    
    @staticmethod
    def calcular_retencion_alumnos(meses=6):
        """Calcula retención de alumnos mes a mes"""
        now = datetime.now().date()
        resultados = []
        
        for i in range(meses):
            mes_inicio = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1)
            mes_fin = (mes_inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            estudiantes_activos = AttendanceStudent.objects.filter(
                id_session__date__range=[mes_inicio, mes_fin]
            ).values('id_student').distinct().count()
            
            resultados.append({
                'mes': mes_inicio.strftime('%Y-%m'),
                'estudiantes_activos': estudiantes_activos
            })
        
        return list(reversed(resultados))
    
    @staticmethod
    def calcular_dia_mayor_asistencia(periodo):
        """Calcula días con mayor participación"""
        now = datetime.now().date()
        
        if periodo == 'semana':
            start_date = now - timedelta(days=now.weekday())
        elif periodo == 'mes':
            start_date = datetime(now.year, now.month, 1).date()
        elif periodo == 'año' or periodo == 'anio':
            start_date = datetime(now.year, 1, 1).date()
        else:
            start_date = now - timedelta(days=30)
        
        # Agrupar por día de la semana
        asistencias_por_dia = AttendanceStudent.objects.filter(
            id_session__date__gte=start_date,
            attendance__in=['ONTIME', 'LATE']
        ).extra(
            select={'dia_semana': 'DAYOFWEEK(id_session.date)'
        }).values('dia_semana').annotate(
            total_asistencias=Count('id')
        ).order_by('-total_asistencias')
        
        # Mapear números a nombres de días
        dias_nombres = {
            1: 'Domingo', 2: 'Lunes', 3: 'Martes', 4: 'Miércoles',
            5: 'Jueves', 6: 'Viernes', 7: 'Sábado'
        }
        
        for item in asistencias_por_dia:
            item['nombre_dia'] = dias_nombres.get(item['dia_semana'], 'Desconocido')
        
        return list(asistencias_por_dia)
    

class GestionService:
    """Servicio para cálculo de métricas de gestión"""
    pass