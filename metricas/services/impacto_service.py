from django.db.models import Count
# from django.db.models.functions import TruncMonth, TruncWeek, Extract
from datetime import datetime, timedelta
from api.models import AttendanceStudent, Session, Students, Class, StudentClass

class ImpactoService:
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
        
        # Contar sesiones y asistencias
        total_sesiones = sessions_query.count()
        total_asistencias = attendance_query.filter(attendance__in=['ONTIME', 'LATE']).count()
        
        # Calcular tasa
        tasa_asistencia = 0
        if total_sesiones > 0 and total_asistencias > 0:
            tasa_asistencia = (total_asistencias / (total_sesiones * AttendanceStudent.objects.values('id_student').distinct().count())) * 100
            
        return {
            'periodo': periodo,
            'tasa_asistencia': round(tasa_asistencia, 2),
            'total_asistencias': total_asistencias,
            'total_sesiones': total_sesiones
        }

    @staticmethod
    def asistencia_por_clase(periodo='mes'):
        """
        Obtiene tasas de asistencia desglosadas por clase para un periodo
        """
        now = datetime.now().date()
        
        if periodo == 'mes':
            start_date = datetime(now.year, now.month, 1).date()
        elif periodo == 'año' or periodo == 'anio':
            start_date = datetime(now.year, 1, 1).date()
        else:
            start_date = now - timedelta(days=30)  # Default: último mes
            
        # Obtener todas las clases activas
        clases = Class.objects.filter(status=1)
        
        resultados = []
        for clase in clases:
            # Para cada clase, calcular su tasa de asistencia
            datos = ImpactoService.calcular_tasa_asistencia(periodo, clase.id)
            
            resultados.append({
                'clase_id': clase.id,
                'clase_nombre': clase.name,
                'dia': clase.day,
                'tasa_asistencia': datos['tasa_asistencia'],
                'total_asistencias': datos['total_asistencias'],
                'total_sesiones': datos['total_sesiones']
            })
            
        return resultados

    @staticmethod
    def alumnos_asistencia_regular(periodo='mes', umbral=0.5):
        """
        Obtiene los alumnos con asistencia regular (>= umbral) para un periodo
        """
        now = datetime.now().date()
        
        if periodo == 'mes':
            start_date = datetime(now.year, now.month, 1).date()
        elif periodo == 'año' or periodo == 'anio':
            start_date = datetime(now.year, 1, 1).date()
        else:
            start_date = now - timedelta(days=30)
            
        # Obtener todos los estudiantes que han asistido al menos una vez en el periodo
        estudiantes_asistentes = AttendanceStudent.objects.filter(
            id_session__date__gte=start_date
        ).values('id_student').distinct()
        
        total_alumnos = estudiantes_asistentes.count()
        alumnos_regulares = []
        total_alumnos_regulares = 0
        
        # Calcular la asistencia para cada estudiante
        for estudiante_data in estudiantes_asistentes:
            estudiante_id = estudiante_data['id_student']
            estudiante = Students.objects.get(id=estudiante_id)
            
            # Contar sesiones totales a las que debería haber asistido
            clases_estudiante = StudentClass.objects.filter(id_student=estudiante_id).values_list('id_class', flat=True)
            sesiones_total = Session.objects.filter(
                id_class__in=clases_estudiante, 
                date__gte=start_date
            ).count()
            
            # Contar asistencias reales
            asistencias = AttendanceStudent.objects.filter(
                id_student=estudiante_id,
                id_session__date__gte=start_date,
                attendance__in=['ONTIME', 'LATE']
            ).count()
            
            # Calcular porcentaje
            porcentaje = 0
            if sesiones_total > 0:
                porcentaje = (asistencias / sesiones_total)
                
            # Verificar si es alumno regular
            if porcentaje >= umbral:
                total_alumnos_regulares += 1
                alumnos_regulares.append({
                    'id': estudiante.id,
                    'nombre': estudiante.name,
                    'apellido': estudiante.last_name,
                    'porcentaje_asistencia': round(porcentaje * 100, 2),
                    'total_asistencias': asistencias,
                    'total_sesiones': sesiones_total
                })
                
        porcentaje_regulares = 0
        if total_alumnos > 0:
            porcentaje_regulares = (total_alumnos_regulares / total_alumnos) * 100
            
        return {
            'porcentaje_alumnos_regulares': round(porcentaje_regulares, 2),
            'total_alumnos_regulares': total_alumnos_regulares,
            'total_alumnos': total_alumnos,
            'alumnos_regulares': alumnos_regulares
        }

    @staticmethod
    def frecuencia_asistencia(periodo='mes'):
        """
        Distribución de alumnos según número de asistencias (1-3, 4-5, 6+)
        """
        now = datetime.now().date()
        
        if periodo == 'mes':
            start_date = datetime(now.year, now.month, 1).date()
        elif periodo == 'año' or periodo == 'anio':
            start_date = datetime(now.year, 1, 1).date()
        else:
            start_date = now - timedelta(days=30)
            
        # Contar asistencias por estudiante
        asistencias_por_estudiante = AttendanceStudent.objects.filter(
            id_session__date__gte=start_date,
            attendance__in=['ONTIME', 'LATE']
        ).values('id_student').annotate(
            num_asistencias=Count('id')
        )
        
        # Clasificar por rangos
        rango_1_3 = 0
        rango_4_5 = 0
        rango_6_mas = 0
        distribucion = {}
        
        for estudiante in asistencias_por_estudiante:
            num = estudiante['num_asistencias']
            
            # Incrementar el contador específico
            if num in distribucion:
                distribucion[num] += 1
            else:
                distribucion[num] = 1
                
            # Clasificar por rango
            if 1 <= num <= 3:
                rango_1_3 += 1
            elif 4 <= num <= 5:
                rango_4_5 += 1
            else:  # 6 o más
                rango_6_mas += 1
                
        return {
            'rango_1_3': rango_1_3,
            'rango_4_5': rango_4_5,
            'rango_6_mas': rango_6_mas,
            'distribucion': distribucion
        }

    @staticmethod
    def retencion_alumnos(periodo_meses=6):
        """
        Número de alumnos que continúan asistiendo mes a mes (últimos N meses)
        """
        now = datetime.now()
        resultados = []
        
        # Analizar los últimos N meses
        for i in range(periodo_meses):
            # Calcular mes actual y anterior
            mes_actual = now - timedelta(days=30 * i)
            mes_anterior = now - timedelta(days=30 * (i + 1))
            
            inicio_mes_actual = datetime(mes_actual.year, mes_actual.month, 1).date()
            fin_mes_actual = datetime(mes_actual.year, mes_actual.month + 1, 1).date() if mes_actual.month < 12 else datetime(mes_actual.year + 1, 1, 1).date()
            inicio_mes_anterior = datetime(mes_anterior.year, mes_anterior.month, 1).date()
            
            # Estudiantes que asistieron el mes actual
            estudiantes_mes_actual = AttendanceStudent.objects.filter(
                id_session__date__gte=inicio_mes_actual,
                id_session__date__lt=fin_mes_actual
            ).values('id_student').distinct()
            
            total_mes_actual = estudiantes_mes_actual.count()
            
            # Estudiantes que también asistieron el mes anterior
            estudiantes_retenidos = AttendanceStudent.objects.filter(
                id_student__in=[e['id_student'] for e in estudiantes_mes_actual],
                id_session__date__gte=inicio_mes_anterior,
                id_session__date__lt=inicio_mes_actual
            ).values('id_student').distinct()
            
            total_retenidos = estudiantes_retenidos.count()
            
            # Estudiantes nuevos (no estaban el mes anterior)
            estudiantes_mes_anterior = AttendanceStudent.objects.filter(
                id_session__date__gte=inicio_mes_anterior,
                id_session__date__lt=inicio_mes_actual
            ).values('id_student').distinct()
            
            nuevos_estudiantes = total_mes_actual - estudiantes_mes_actual.filter(
                id_student__in=[e['id_student'] for e in estudiantes_mes_anterior]
            ).count()
            
            # Calcular tasa de retención
            tasa_retencion = 0
            if estudiantes_mes_anterior.count() > 0:
                tasa_retencion = (total_retenidos / estudiantes_mes_anterior.count()) * 100
                
            resultados.append({
                'mes': f"{mes_actual.strftime('%B')} {mes_actual.year}",
                'total_alumnos': total_mes_actual,
                'nuevos_alumnos': nuevos_estudiantes,
                'alumnos_retenidos': total_retenidos,
                'tasa_retencion': round(tasa_retencion, 2)
            })
            
        return resultados

    @staticmethod
    def dia_mayor_asistencia(periodo='mes'):
        """
        Identificar qué días hay mayor o menor participación
        """
        now = datetime.now().date()
        
        if periodo == 'mes':
            start_date = datetime(now.year, now.month, 1).date()
        elif periodo == 'año' or periodo == 'anio':
            start_date = datetime(now.year, 1, 1).date()
        else:
            start_date = now - timedelta(days=30)
            
        # Contar asistencias por día de la semana
        asistencias_por_dia = {}
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        
        for i in range(7):
            asistencias_por_dia[dias_semana[i]] = AttendanceStudent.objects.filter(
                id_session__date__gte=start_date,
                id_session__date__week_day=i+2,  # En Django, 1=Domingo, 2=Lunes, etc.
                attendance__in=['ONTIME', 'LATE']
            ).count()
            
        # Encontrar el día con mayor asistencia
        dia_mayor = max(asistencias_por_dia, key=asistencias_por_dia.get)
            
        return {
            'dia_mayor_asistencia': dia_mayor,
            'asistencias_por_dia': asistencias_por_dia
        }

    @staticmethod
    def promedio_sesiones(periodo='mes'):
        """
        Promedio de sesiones asistidas por alumno
        """
        now = datetime.now().date()
        
        if periodo == 'mes':
            start_date = datetime(now.year, now.month, 1).date()
        elif periodo == 'año' or periodo == 'anio':
            start_date = datetime(now.year, 1, 1).date()
        else:
            start_date = now - timedelta(days=30)
            
        # Estudiantes que han asistido al menos una vez
        estudiantes = AttendanceStudent.objects.filter(
            id_session__date__gte=start_date
        ).values('id_student').distinct()
        
        total_alumnos = estudiantes.count()
        
        # Total de asistencias
        total_asistencias = AttendanceStudent.objects.filter(
            id_session__date__gte=start_date,
            attendance__in=['ONTIME', 'LATE']
        ).count()
        
        # Calcular promedio
        promedio = 0
        if total_alumnos > 0:
            promedio = total_asistencias / total_alumnos
            
        return {
            'promedio_sesiones': round(promedio, 2),
            'total_asistencias': total_asistencias,
            'total_alumnos': total_alumnos
        }