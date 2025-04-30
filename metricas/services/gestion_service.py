# from django.db.models import Count, Sum, Avg, F, Q, Case, When, Value, IntegerField
# from django.db.models.functions import TruncMonth, TruncWeek
from datetime import datetime, timedelta, date
from api.models import AttendanceStudent, Session, Students, Class

class GestionService:
    @staticmethod
    def _calcular_edad(birthdate):
        """Calcula la edad en años a partir de la fecha de nacimiento"""
        if not birthdate:
            return None
        today = date.today()
        return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

    @staticmethod
    def lista_asistencia_diaria(fecha=None, clase_id=None):
        """
        Obtiene la lista de asistencia para un día específico
        """
        if not fecha:
            fecha = datetime.now().date()
            
        # Obtener las sesiones del día
        sesiones_query = Session.objects.filter(date__date=fecha)
        
        if clase_id:
            sesiones_query = sesiones_query.filter(id_class=clase_id)
        
        if not sesiones_query.exists():
            clase_nombre = "Todas las clases" if not clase_id else Class.objects.get(id=clase_id).name
            return {
                'fecha': fecha,
                'clase': clase_nombre,
                'total_alumnos': 0,
                'alumnos': []
            }
        
        # Si no se especifica clase, usar la primera sesión encontrada
        if not clase_id and sesiones_query.exists():
            sesion = sesiones_query.first()
            clase_id = sesion.id_class.id
            clase_nombre = sesion.id_class.name
        else:
            clase_nombre = Class.objects.get(id=clase_id).name
        
        # Obtener la asistencia para esas sesiones
        asistencias = AttendanceStudent.objects.filter(
            id_session__in=sesiones_query.filter(id_class=clase_id)
        ).select_related('id_student')
        
        alumnos = []
        for asistencia in asistencias:
            alumno = asistencia.id_student
            alumnos.append({
                'id': alumno.id,
                'nombre': alumno.name,
                'apellido': alumno.last_name,
                'genero': alumno.gender or 'No especificado',
                'edad': GestionService._calcular_edad(alumno.birthdate),
                'asistencia': asistencia.attendance or 'No registrada'
            })
            
        return {
            'fecha': fecha,
            'clase': clase_nombre,
            'total_alumnos': len(alumnos),
            'alumnos': alumnos
        }

    @staticmethod
    def lista_asistencia_semanal(fecha_inicio=None, clase_id=None):
        """
        Obtiene la lista de asistencia semanal con estadísticas
        """
        now = datetime.now().date()
        
        if not fecha_inicio:
            # Inicio de la semana actual (lunes)
            fecha_inicio = now - timedelta(days=now.weekday())
            
        fecha_fin = fecha_inicio + timedelta(days=6)
        
        # Filtro base para sesiones en el rango de fechas
        sesiones_query = Session.objects.filter(
            date__date__gte=fecha_inicio,
            date__date__lte=fecha_fin
        )
        
        if clase_id:
            sesiones_query = sesiones_query.filter(id_class=clase_id)
            
        # Si no hay sesiones en la fecha, retornar resultado vacío
        if not sesiones_query.exists():
            return {
                'semana_inicio': fecha_inicio,
                'semana_fin': fecha_fin,
                'total_alumnos': 0,
                'total_sesiones': 0,
                'alumnos': []
            }
            
        # IDs de estudiantes con asistencia registrada
        estudiantes_ids = AttendanceStudent.objects.filter(
            id_session__in=sesiones_query
        ).values_list('id_student', flat=True).distinct()
        
        estudiantes = Students.objects.filter(id__in=estudiantes_ids)
        total_sesiones = sesiones_query.count()
        
        alumnos_data = []
        for estudiante in estudiantes:
            # Contar asistencias del estudiante
            asistencias = AttendanceStudent.objects.filter(
                id_student=estudiante.id,
                id_session__in=sesiones_query,
                attendance__in=['ONTIME', 'LATE']
            ).count()
            
            # Calcular porcentaje de asistencia
            porcentaje = (asistencias / total_sesiones * 100) if total_sesiones > 0 else 0
            
            # Determinar estatus
            if porcentaje >= 50:
                estatus = 'regular'
            elif porcentaje > 0:
                estatus = 'baja asistencia'
            else:
                estatus = 'ausente'
                
            alumnos_data.append({
                'id': estudiante.id,
                'nombre': estudiante.name,
                'apellido': estudiante.last_name,
                'genero': estudiante.gender or 'No especificado',
                'edad': GestionService._calcular_edad(estudiante.birthdate),
                'total_asistencias': asistencias,
                'total_sesiones': total_sesiones,
                'porcentaje_asistencia': round(porcentaje, 2),
                'estatus': estatus
            })
            
        return {
            'semana_inicio': fecha_inicio,
            'semana_fin': fecha_fin,
            'total_alumnos': len(alumnos_data),
            'total_sesiones': total_sesiones,
            'alumnos': alumnos_data
        }
        
    @staticmethod
    def lista_asistencia_mensual(mes=None, anio=None, clase_id=None):
        """
        Obtiene la lista de asistencia mensual con estadísticas
        """
        now = datetime.now()
        
        # Si no se especifican mes o año, usar el actual
        if not mes:
            mes = now.month
        if not anio:
            anio = now.year
            
        # Fechas de inicio y fin del mes
        fecha_inicio = datetime(anio, mes, 1).date()
        if mes == 12:
            fecha_fin = datetime(anio + 1, 1, 1).date() - timedelta(days=1)
        else:
            fecha_fin = datetime(anio, mes + 1, 1).date() - timedelta(days=1)
            
        # Filtro base para sesiones en el mes
        sesiones_query = Session.objects.filter(
            date__date__gte=fecha_inicio,
            date__date__lte=fecha_fin
        )
        
        if clase_id:
            sesiones_query = sesiones_query.filter(id_class=clase_id)
            
        # Si no hay sesiones en el mes, retornar resultado vacío
        if not sesiones_query.exists():
            return {
                'mes': fecha_inicio.strftime('%B'),
                'anio': anio,
                'total_alumnos': 0,
                'total_sesiones': 0,
                'alumnos': []
            }
            
        # IDs de estudiantes con asistencia registrada
        estudiantes_ids = AttendanceStudent.objects.filter(
            id_session__in=sesiones_query
        ).values_list('id_student', flat=True).distinct()
        
        estudiantes = Students.objects.filter(id__in=estudiantes_ids)
        total_sesiones = sesiones_query.count()
        
        alumnos_data = []
        for estudiante in estudiantes:
            # Contar asistencias del estudiante
            asistencias = AttendanceStudent.objects.filter(
                id_student=estudiante.id,
                id_session__in=sesiones_query,
                attendance__in=['ONTIME', 'LATE']
            ).count()
            
            # Calcular porcentaje de asistencia
            porcentaje = (asistencias / total_sesiones * 100) if total_sesiones > 0 else 0
            
            # Determinar estatus
            if porcentaje >= 50:
                estatus = 'regular'
            elif porcentaje > 25:
                estatus = 'baja asistencia'
            else:
                estatus = 'ausente'
                
            alumnos_data.append({
                'id': estudiante.id,
                'nombre': estudiante.name,
                'apellido': estudiante.last_name,
                'genero': estudiante.gender or 'No especificado',
                'edad': GestionService._calcular_edad(estudiante.birthdate),
                'total_asistencias': asistencias,
                'total_sesiones': total_sesiones,
                'porcentaje_asistencia': round(porcentaje, 2),
                'estatus': estatus
            })
            
        return {
            'mes': fecha_inicio.strftime('%B'),
            'anio': anio,
            'total_alumnos': len(alumnos_data),
            'total_sesiones': total_sesiones,
            'alumnos': sorted(alumnos_data, key=lambda x: x['porcentaje_asistencia'], reverse=True)
        }
    
    @staticmethod
    def alumnos_asistencia_irregular(periodo='mes', umbral=0.25):
        """
        Identifica alumnos con asistencia irregular (menos del 25% del total de sesiones)
        """
        now = datetime.now().date()
        
        # Determinar fecha de inicio según el periodo
        if periodo == 'semana':
            fecha_inicio = now - timedelta(days=now.weekday())
        elif periodo == 'mes':
            fecha_inicio = datetime(now.year, now.month, 1).date()
        elif periodo == 'año':
            fecha_inicio = datetime(now.year, 1, 1).date()
        else:
            fecha_inicio = now - timedelta(days=30)  # Default: último mes
        
        # Obtener sesiones en el periodo
        sesiones = Session.objects.filter(date__date__gte=fecha_inicio)
        total_sesiones = sesiones.count()
        
        if total_sesiones == 0:
            return {
                'periodo': periodo,
                'umbral': umbral * 100,
                'total_alumnos_irregulares': 0,
                'porcentaje': 0,
                'alumnos': []
            }
        
        # Obtener todos los estudiantes que han asistido al menos a una sesión
        estudiantes_ids = AttendanceStudent.objects.filter(
            id_session__in=sesiones
        ).values_list('id_student', flat=True).distinct()
        
        total_estudiantes = len(estudiantes_ids)
        alumnos_irregulares = []
        
        for estudiante_id in estudiantes_ids:
            # Contar sesiones asistidas
            asistencias = AttendanceStudent.objects.filter(
                id_student=estudiante_id,
                id_session__in=sesiones,
                attendance__in=['ONTIME', 'LATE']
            ).count()
            
            # Calcular porcentaje de asistencia
            porcentaje = asistencias / total_sesiones if total_sesiones > 0 else 0
            
            # Si es menor que el umbral, es irregular
            if porcentaje < umbral:
                estudiante = Students.objects.get(id=estudiante_id)
                alumnos_irregulares.append({
                    'id': estudiante.id,
                    'nombre': estudiante.name,
                    'apellido': estudiante.last_name,
                    'genero': estudiante.gender or 'No especificado',
                    'edad': GestionService._calcular_edad(estudiante.birthdate),
                    'asistencias': asistencias,
                    'total_sesiones': total_sesiones,
                    'porcentaje_asistencia': round(porcentaje * 100, 2)
                })
        
        porcentaje_irregulares = (len(alumnos_irregulares) / total_estudiantes * 100) if total_estudiantes > 0 else 0
                
        return {
            'periodo': periodo,
            'umbral': umbral * 100,
            'total_alumnos_irregulares': len(alumnos_irregulares),
            'porcentaje': round(porcentaje_irregulares, 2),
            'alumnos': alumnos_irregulares
        }
    
    @staticmethod
    def analisis_grupos_asistencia(criterio='sexo', periodo='mes'):
        """
        Analiza la asistencia por grupos (sexo, edad)
        """
        now = datetime.now().date()
        
        # Determinar fecha de inicio según el periodo
        if periodo == 'semana':
            fecha_inicio = now - timedelta(days=now.weekday())
        elif periodo == 'mes':
            fecha_inicio = datetime(now.year, now.month, 1).date()
        elif periodo == 'año':
            fecha_inicio = datetime(now.year, 1, 1).date()
        else:
            fecha_inicio = now - timedelta(days=30)  # Default: último mes
            
        # Obtener sesiones y asistencias en el periodo
        sesiones = Session.objects.filter(date__date__gte=fecha_inicio)
        
        if criterio == 'sexo':
            # Agrupar estudiantes por género
            estudiantes_masculino = Students.objects.filter(gender='Masculino')
            estudiantes_femenino = Students.objects.filter(gender='Femenino')
            estudiantes_otro = Students.objects.exclude(gender__in=['Masculino', 'Femenino'])
            
            # Para cada grupo, calcular asistencia
            asistencia_masculino = AttendanceStudent.objects.filter(
                id_student__in=estudiantes_masculino,
                id_session__in=sesiones,
                attendance__in=['ONTIME', 'LATE']
            ).count()
            
            asistencia_femenino = AttendanceStudent.objects.filter(
                id_student__in=estudiantes_femenino,
                id_session__in=sesiones,
                attendance__in=['ONTIME', 'LATE']
            ).count()
            
            asistencia_otro = AttendanceStudent.objects.filter(
                id_student__in=estudiantes_otro,
                id_session__in=sesiones,
                attendance__in=['ONTIME', 'LATE']
            ).count()
            
            # Calcular totales posibles
            total_posible_masculino = len(estudiantes_masculino) * sesiones.count()
            total_posible_femenino = len(estudiantes_femenino) * sesiones.count()
            total_posible_otro = len(estudiantes_otro) * sesiones.count()
            
            # Calcular porcentajes
            porcentaje_masculino = (asistencia_masculino / total_posible_masculino * 100) if total_posible_masculino > 0 else 0
            porcentaje_femenino = (asistencia_femenino / total_posible_femenino * 100) if total_posible_femenino > 0 else 0
            porcentaje_otro = (asistencia_otro / total_posible_otro * 100) if total_posible_otro > 0 else 0
            
            grupos = {
                'Masculino': {
                    'total_estudiantes': len(estudiantes_masculino),
                    'asistencias': asistencia_masculino,
                    'porcentaje': round(porcentaje_masculino, 2)
                },
                'Femenino': {
                    'total_estudiantes': len(estudiantes_femenino),
                    'asistencias': asistencia_femenino,
                    'porcentaje': round(porcentaje_femenino, 2)
                },
                'Otro': {
                    'total_estudiantes': len(estudiantes_otro),
                    'asistencias': asistencia_otro,
                    'porcentaje': round(porcentaje_otro, 2)
                }
            }
            
        elif criterio == 'edad':
            # Definir rangos de edad
            rangos_edad = {
                '0-5': {'min': 0, 'max': 5},
                '6-12': {'min': 6, 'max': 12},
                '13-17': {'min': 13, 'max': 17},
                '18+': {'min': 18, 'max': 150}
            }
            
            grupos = {}
            for rango_nombre, rango_valores in rangos_edad.items():
                # Filtrar estudiantes por edad
                estudiantes_rango = []
                for estudiante in Students.objects.all():
                    edad = GestionService._calcular_edad(estudiante.birthdate)
                    if edad and rango_valores['min'] <= edad <= rango_valores['max']:
                        estudiantes_rango.append(estudiante.id)
                
                # Contar asistencias para este rango
                asistencias_rango = AttendanceStudent.objects.filter(
                    id_student__in=estudiantes_rango,
                    id_session__in=sesiones,
                    attendance__in=['ONTIME', 'LATE']
                ).count()
                
                # Calcular total posible
                total_posible = len(estudiantes_rango) * sesiones.count()
                
                # Calcular porcentaje
                porcentaje = (asistencias_rango / total_posible * 100) if total_posible > 0 else 0
                
                grupos[rango_nombre] = {
                    'total_estudiantes': len(estudiantes_rango),
                    'asistencias': asistencias_rango,
                    'porcentaje': round(porcentaje, 2)
                }
                
        else:
            grupos = {}
            
        return {
            'criterio': criterio,
            'periodo': periodo,
            'grupos': grupos
        }
    
    @staticmethod
    def alumnos_inactivos(dias=30):
        """
        Lista de alumnos que no han asistido en los últimos X días
        """
        fecha_limite = datetime.now().date() - timedelta(days=dias)
        
        # Todos los estudiantes activos
        estudiantes = Students.objects.filter(status=1)
        
        alumnos_inactivos = []
        for estudiante in estudiantes:
            # Buscar la última asistencia
            ultima_asistencia = AttendanceStudent.objects.filter(
                id_student=estudiante.id,
                attendance__in=['ONTIME', 'LATE']
            ).order_by('-id_session__date').first()
            
            # Si no hay asistencia o es anterior a la fecha límite
            if not ultima_asistencia or (ultima_asistencia.id_session.date.date() < fecha_limite):
                dias_inactividad = None
                if ultima_asistencia:
                    dias_inactividad = (datetime.now().date() - ultima_asistencia.id_session.date.date()).days
                
                alumnos_inactivos.append({
                    'id': estudiante.id,
                    'nombre': estudiante.name,
                    'apellido': estudiante.last_name,
                    'genero': estudiante.gender or 'No especificado',
                    'edad': GestionService._calcular_edad(estudiante.birthdate),
                    'ultima_asistencia': ultima_asistencia.id_session.date.date() if ultima_asistencia else None,
                    'dias_inactividad': dias_inactividad,
                    'clases': [sc.id_class.name for sc in estudiante.studentclass_set.all()]
                })
        
        return {
            'dias_inactividad_limite': dias,
            'total_alumnos_inactivos': len(alumnos_inactivos),
            'alumnos': sorted(alumnos_inactivos, key=lambda x: x['dias_inactividad'] if x['dias_inactividad'] else float('inf'), reverse=True)
        }