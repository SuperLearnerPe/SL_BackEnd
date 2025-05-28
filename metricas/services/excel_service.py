# filepath: c:\Users\USUARIO\Desktop\SL_BackEnd\metricas\services\excel_service_fixed.py
import pandas as pd
import io
from datetime import datetime, date, timedelta
from django.db.models import Count, Q
from api.models import AttendanceStudent, Students, Class, Session

class ExcelService:
    @staticmethod
    def _calcular_edad(birthdate):
        """Calcula la edad en años a partir de la fecha de nacimiento"""
        if not birthdate:
            return None
        today = date.today()
        return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    
    @staticmethod
    def generar_excel_impacto(periodo='mes', umbral_regular=0.5):
        """
        Genera un informe Excel con métricas de impacto según requerimientos:
        - Tasa de asistencia por clase/día y general
        - Porcentaje de alumnos regulares (≥50%)
        - Frecuencia de asistencia (1-3, 4-5, 6+)
        - Retención mes a mes
        - Día con mayor asistencia
        - Promedio de sesiones por alumno
        """
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        
        # Determinar período de análisis
        now = date.today()
        if periodo == 'semana':
            start_date = now - timedelta(days=now.weekday())
            titulo_periodo = f"Semana del {start_date}"
        elif periodo == 'mes':
            start_date = date(now.year, now.month, 1)
            titulo_periodo = f"{now.strftime('%B %Y')}"
        elif periodo == 'año':
            start_date = date(now.year, 1, 1)
            titulo_periodo = f"Año {now.year}"
        else:
            start_date = now - timedelta(days=30)
            titulo_periodo = "Últimos 30 días"
        
        # 1. TASA DE ASISTENCIA GENERAL
        total_sesiones_programadas = Session.objects.filter(date__gte=start_date).count()
        total_asistencias = AttendanceStudent.objects.filter(
            id_session__date__gte=start_date,
            attendance='PRESENT'
        ).count()
        tasa_general = (total_asistencias / total_sesiones_programadas * 100) if total_sesiones_programadas > 0 else 0
        
        datos_generales = {
            'Métrica': [
                f'Tasa de Asistencia General - {titulo_periodo} (%)',
                'Total de Asistencias',
                'Total de Sesiones Programadas', 
                'Total Estudiantes Únicos'
            ],
            'Valor': [
                round(tasa_general, 2),
                total_asistencias,
                total_sesiones_programadas,
                Students.objects.count()
            ]
        }
        df_general = pd.DataFrame(datos_generales)
        df_general.to_excel(writer, sheet_name='Tasa Asistencia General', index=False)
          # 2. TASA DE ASISTENCIA POR CLASE/DÍA
        # Optimización: Una sola consulta para todas las clases
        clases_con_datos = Class.objects.prefetch_related(
            'session_set',
            'session_set__attendancestudent_set'
        ).annotate(
            sesiones_periodo=Count('session', filter=Q(session__date__gte=start_date)),
            asistencias_periodo=Count('session__attendancestudent', 
                                    filter=Q(session__date__gte=start_date, 
                                            session__attendancestudent__attendance='PRESENT'))
        )
        
        clases_data = []
        for clase in clases_con_datos:
            tasa_clase = (clase.asistencias_periodo / clase.sesiones_periodo * 100) if clase.sesiones_periodo > 0 else 0
            
            clases_data.append({
                'ID Clase': clase.id,
                'Nombre Clase': clase.name,
                'Día': clase.day,
                'Hora': f"{clase.start_time} - {clase.end_time}",
                'Sesiones Programadas': clase.sesiones_periodo,
                'Total Asistencias': clase.asistencias_periodo,
                'Tasa Asistencia (%)': round(tasa_clase, 2)
            })
        
        df_clases = pd.DataFrame(clases_data)
        df_clases.to_excel(writer, sheet_name='Tasa por Clase-Día', index=False)
          # 3. ALUMNOS CON ASISTENCIA REGULAR (≥50%)
        # Optimización: calcular sesiones totales una sola vez
        total_sesiones_periodo = Session.objects.filter(date__gte=start_date).count()
        
        # Optimización: obtener todas las asistencias del período con datos relacionados
        asistencias_periodo = AttendanceStudent.objects.filter(
            id_session__date__gte=start_date,
            attendance='PRESENT'
        ).select_related('id_student').values('id_student__id', 'id_student__name', 
                                             'id_student__last_name', 'id_student__gender', 
                                             'id_student__birthdate')
        
        # Contar asistencias por estudiante
        from collections import defaultdict
        asistencias_por_estudiante = defaultdict(int)
        estudiantes_data = {}
        
        for asistencia in asistencias_periodo:
            est_id = asistencia['id_student__id']
            asistencias_por_estudiante[est_id] += 1
            estudiantes_data[est_id] = {
                'name': asistencia['id_student__name'],
                'last_name': asistencia['id_student__last_name'], 
                'gender': asistencia['id_student__gender'],
                'birthdate': asistencia['id_student__birthdate']
            }
        
        total_alumnos_asistentes = len(estudiantes_data)
        alumnos_regulares = []
        
        for est_id, asistencias_count in asistencias_por_estudiante.items():
            porcentaje = (asistencias_count / total_sesiones_periodo * 100) if total_sesiones_periodo > 0 else 0
            
            if porcentaje >= 50:  # Exactamente ≥50% según requerimientos
                est_data = estudiantes_data[est_id]
                alumnos_regulares.append({
                    'ID': est_id,
                    'Nombre': est_data['name'],
                    'Apellido': est_data['last_name'],
                    'Género': est_data['gender'],
                    'Edad': ExcelService._calcular_edad(est_data['birthdate']),
                    'Total Asistencias': asistencias_count,
                    'Total Sesiones': total_sesiones_periodo,
                    'Porcentaje Asistencia (%)': round(porcentaje, 2),
                    'Estatus': 'Regular'
                })
        
        porcentaje_regulares = (len(alumnos_regulares) / total_alumnos_asistentes * 100) if total_alumnos_asistentes > 0 else 0
        
        # Crear resumen y lista de alumnos regulares
        resumen_regulares = {
            'Métrica': [
                f'Porcentaje de Alumnos Regulares - {titulo_periodo}',
                'Total Alumnos Regulares (≥50%)',
                'Total Alumnos Asistentes',
                'Fórmula'
            ],
            'Valor': [
                f"{round(porcentaje_regulares, 2)}%",
                len(alumnos_regulares),
                total_alumnos_asistentes,
                'Alumnos ≥50% asistencia / Total alumnos asistentes × 100%'
            ]
        }
        df_resumen_reg = pd.DataFrame(resumen_regulares)
        df_regulares = pd.DataFrame(alumnos_regulares)
        
        # Escribir en una sola hoja combinando ambos DataFrames
        df_resumen_reg.to_excel(writer, sheet_name='Alumnos Regulares', startrow=0, index=False)
        if not df_regulares.empty:
            df_regulares.to_excel(writer, sheet_name='Alumnos Regulares', startrow=len(df_resumen_reg) + 2, index=False)
          # 4. FRECUENCIA DE ASISTENCIA (1-3, 4-5, 6+)
        rango_1_3 = 0
        rango_4_5 = 0  
        rango_6_mas = 0
        
        for est_id, asistencias_count in asistencias_por_estudiante.items():
            if 1 <= asistencias_count <= 3:
                rango_1_3 += 1
            elif 4 <= asistencias_count <= 5:
                rango_4_5 += 1
            elif asistencias_count >= 6:
                rango_6_mas += 1
        
        frecuencia_data = {
            'Rango de Asistencias': ['1-3 veces', '4-5 veces', '6 o más veces'],
            'Cantidad de Alumnos': [rango_1_3, rango_4_5, rango_6_mas],
            'Porcentaje': [
                round((rango_1_3/total_alumnos_asistentes*100), 2) if total_alumnos_asistentes > 0 else 0,
                round((rango_4_5/total_alumnos_asistentes*100), 2) if total_alumnos_asistentes > 0 else 0,
                round((rango_6_mas/total_alumnos_asistentes*100), 2) if total_alumnos_asistentes > 0 else 0
            ]
        }
        df_frecuencia = pd.DataFrame(frecuencia_data)
        df_frecuencia.to_excel(writer, sheet_name='Frecuencia Asistencia', index=False)
        
        # 5. RETENCIÓN MES A MES (últimos 6 meses)
        retencion_data = []
        for i in range(6):
            mes_actual = now - timedelta(days=30 * i)
            mes_anterior = now - timedelta(days=30 * (i + 1))
            
            inicio_mes_actual = date(mes_actual.year, mes_actual.month, 1)
            if mes_actual.month == 12:
                inicio_mes_siguiente = date(mes_actual.year + 1, 1, 1)
            else:
                inicio_mes_siguiente = date(mes_actual.year, mes_actual.month + 1, 1)
            
            inicio_mes_anterior = date(mes_anterior.year, mes_anterior.month, 1)
            
            # Estudiantes que asistieron el mes actual
            estudiantes_mes_actual = AttendanceStudent.objects.filter(
                id_session__date__gte=inicio_mes_actual,
                id_session__date__lt=inicio_mes_siguiente,
                attendance='PRESENT'
            ).values('id_student').distinct()
            
            # Estudiantes que también asistieron el mes anterior
            estudiantes_mes_anterior = AttendanceStudent.objects.filter(
                id_session__date__gte=inicio_mes_anterior,
                id_session__date__lt=inicio_mes_actual,
                attendance='PRESENT'
            ).values('id_student').distinct()
            
            # Estudiantes retenidos (estuvieron en ambos meses)
            ids_mes_actual = set([e['id_student'] for e in estudiantes_mes_actual])
            ids_mes_anterior = set([e['id_student'] for e in estudiantes_mes_anterior])
            retenidos = len(ids_mes_actual.intersection(ids_mes_anterior))
            
            tasa_retencion = (retenidos / len(ids_mes_anterior) * 100) if ids_mes_anterior else 0
            
            retencion_data.append({
                'Mes': mes_actual.strftime('%B %Y'),
                'Total Alumnos Mes Actual': len(ids_mes_actual),
                'Total Alumnos Mes Anterior': len(ids_mes_anterior),
                'Alumnos Retenidos': retenidos,
                'Tasa Retención (%)': round(tasa_retencion, 2)
            })
        
        df_retencion = pd.DataFrame(retencion_data)
        df_retencion.to_excel(writer, sheet_name='Retención Mes a Mes', index=False)
        
        # 6. DÍA CON MAYOR ASISTENCIA
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        asistencias_por_dia = {}
        
        for i in range(7):
            # Django: 1=Domingo, 2=Lunes, 3=Martes, 4=Miércoles, 5=Jueves, 6=Viernes, 7=Sábado
            # Convertir índice de lista (0=Lunes) a número de Django
            django_day_mapping = {
                0: 2,  # Lunes
                1: 3,  # Martes
                2: 4,  # Miércoles
                3: 5,  # Jueves
                4: 6,  # Viernes
                5: 7,  # Sábado
                6: 1   # Domingo
            }
            dia_semana_num = django_day_mapping[i]
            
            asistencias_dia = AttendanceStudent.objects.filter(
                id_session__date__gte=start_date,
                id_session__date__week_day=dia_semana_num,
                attendance='PRESENT'
            ).count()
            
            asistencias_por_dia[dias_semana[i]] = asistencias_dia
        
        dia_mayor = max(asistencias_por_dia, key=asistencias_por_dia.get) if asistencias_por_dia else 'N/A'
        
        dias_data = []
        for dia, asistencias in asistencias_por_dia.items():
            dias_data.append({
                'Día de la Semana': dia,
                'Total Asistencias': asistencias,
                'Es Día Mayor': 'Sí' if dia == dia_mayor else 'No'
            })
        
        df_dias = pd.DataFrame(dias_data)
        df_dias.to_excel(writer, sheet_name='Día Mayor Asistencia', index=False)
        
        # 7. PROMEDIO DE SESIONES POR ALUMNO
        total_asistencias_unicas = AttendanceStudent.objects.filter(
            id_session__date__gte=start_date,
            attendance='PRESENT'
        ).count()
        
        total_alumnos_unicos = AttendanceStudent.objects.filter(
            id_session__date__gte=start_date
        ).values('id_student').distinct().count()
        
        promedio_sesiones = (total_asistencias_unicas / total_alumnos_unicos) if total_alumnos_unicos > 0 else 0
        
        promedio_data = {
            'Métrica': [
                f'Promedio de Sesiones por Alumno - {titulo_periodo}',
                'Total de Asistencias',
                'Total de Alumnos Únicos',
                'Fórmula'
            ],
            'Valor': [
                round(promedio_sesiones, 2),
                total_asistencias_unicas,
                total_alumnos_unicos,
                'Total de Asistencias / Total de Alumnos que asistieron al menos 1 vez'
            ]
        }
        df_promedio = pd.DataFrame(promedio_data)
        df_promedio.to_excel(writer, sheet_name='Promedio Sesiones Alumno', index=False)
        
        # Cerrar el writer y devolver el buffer
        writer.close()
        output.seek(0)
        
        return output
    
    @staticmethod
    def generar_excel_gestion(fecha=None, fecha_inicio=None, mes=None, anio=None, 
                            clase_id=None, umbral_irregular=0.25, criterio='sexo', dias_inactivos=30):
        """
        Genera un informe Excel con métricas de gestión según requerimientos:
        - Lista diaria: nombre, sexo, edad
        - Lista semanal: nombre, sexo, edad, total asistencias, porcentaje, estatus
        - Lista mensual: nombre, sexo, edad, total asistencias, porcentaje, estatus
        - Alumnos irregulares: <25% asistencia
        - Grupos por sexo/edad
        - Alumnos con más de 30 faltas seguidas
        """
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        
        # 1. LISTA DE ASISTENCIA DIARIA (si se especifica fecha)
        if fecha:
            try:
                fecha_obj = datetime.strptime(str(fecha), '%Y-%m-%d').date()
                
                query_filter = {'id_session__date': fecha_obj}
                if clase_id:
                    query_filter['id_session__id_class__id'] = clase_id
                
                asistencias_diarias = AttendanceStudent.objects.filter(**query_filter).select_related(
                    'id_student', 'id_session__id_class'
                )
                
                datos_diarios = []
                for asistencia in asistencias_diarias:
                    datos_diarios.append({
                        'ID Estudiante': asistencia.id_student.id,
                        'Nombre': asistencia.id_student.name,
                        'Apellido': asistencia.id_student.last_name,
                        'Sexo': asistencia.id_student.gender,
                        'Edad': ExcelService._calcular_edad(asistencia.id_student.birthdate),
                        'Clase': asistencia.id_session.id_class.name,
                        'Sesión': asistencia.id_session.num_session,
                        'Asistencia': asistencia.attendance or 'No Registrado',
                        'Fecha': fecha_obj
                    })
                
                df_diario = pd.DataFrame(datos_diarios)
                df_diario.to_excel(writer, sheet_name='Lista Asistencia Diaria', index=False)
            except Exception as e:
                df_diario = pd.DataFrame({'Mensaje': [f'Error con fecha: {str(e)}']})
                df_diario.to_excel(writer, sheet_name='Lista Asistencia Diaria', index=False)
        
        # 2. LISTA DE ASISTENCIA SEMANAL (con estatus)
        if fecha_inicio:
            fecha_fin = fecha_inicio + timedelta(days=6)
            
            query_filter = {
                'id_session__date__gte': fecha_inicio,
                'id_session__date__lte': fecha_fin
            }
            if clase_id:
                query_filter['id_session__id_class__id'] = clase_id
            
            # Obtener estudiantes y calcular estadísticas
            estudiantes_semana = {}
            asistencias_semana = AttendanceStudent.objects.filter(**query_filter).select_related('id_student')
            
            total_sesiones_semana = Session.objects.filter(
                date__gte=fecha_inicio,
                date__lte=fecha_fin
            ).count()
            
            for asistencia in asistencias_semana:
                est_id = asistencia.id_student.id
                if est_id not in estudiantes_semana:
                    estudiantes_semana[est_id] = {
                        'estudiante': asistencia.id_student,
                        'presentes': 0,
                        'total_registros': 0
                    }
                
                estudiantes_semana[est_id]['total_registros'] += 1
                if asistencia.attendance == 'PRESENT':
                    estudiantes_semana[est_id]['presentes'] += 1
            
            datos_semanales = []
            for est_data in estudiantes_semana.values():
                porcentaje = (est_data['presentes'] / total_sesiones_semana * 100) if total_sesiones_semana > 0 else 0
                
                # Determinar estatus según requerimientos
                if porcentaje >= 50:
                    estatus = 'regular'
                elif porcentaje > 0:
                    estatus = 'baja asistencia'
                else:
                    estatus = 'ausente'
                
                datos_semanales.append({
                    'ID': est_data['estudiante'].id,
                    'Nombre': est_data['estudiante'].name,
                    'Apellido': est_data['estudiante'].last_name,
                    'Sexo': est_data['estudiante'].gender,
                    'Edad': ExcelService._calcular_edad(est_data['estudiante'].birthdate),
                    'Total Asistencias': est_data['presentes'],
                    'Total Sesiones': total_sesiones_semana,
                    'Porcentaje Asistencia (%)': round(porcentaje, 2),
                    'Estatus': estatus
                })
            
            df_semanal = pd.DataFrame(datos_semanales)
            df_semanal.to_excel(writer, sheet_name='Lista Asistencia Semanal', index=False)
        
        # 3. LISTA DE ASISTENCIA MENSUAL (con estatus)
        if mes and anio:
            query_filter = {
                'id_session__date__month': mes,
                'id_session__date__year': anio
            }
            if clase_id:
                query_filter['id_session__id_class__id'] = clase_id
            
            # Obtener estudiantes y calcular estadísticas
            estudiantes_mes = {}
            asistencias_mes = AttendanceStudent.objects.filter(**query_filter).select_related('id_student')
            total_sesiones_mes = Session.objects.filter(
                date__month=mes,
                date__year=anio
            ).count()
            
            for asistencia in asistencias_mes:
                est_id = asistencia.id_student.id
                if est_id not in estudiantes_mes:
                    estudiantes_mes[est_id] = {
                        'estudiante': asistencia.id_student,
                        'presentes': 0,
                        'total_registros': 0
                    }
                
                estudiantes_mes[est_id]['total_registros'] += 1
                if asistencia.attendance == 'PRESENT':
                    estudiantes_mes[est_id]['presentes'] += 1
            
            datos_mensuales = []
            for est_data in estudiantes_mes.values():
                porcentaje = (est_data['presentes'] / total_sesiones_mes * 100) if total_sesiones_mes > 0 else 0
                
                # Determinar estatus según requerimientos
                if porcentaje >= 50:
                    estatus = 'regular'
                elif porcentaje >= 25:
                    estatus = 'baja asistencia'
                else:
                    estatus = 'ausente'
                
                datos_mensuales.append({
                    'ID': est_data['estudiante'].id,
                    'Nombre': est_data['estudiante'].name,
                    'Apellido': est_data['estudiante'].last_name,
                    'Sexo': est_data['estudiante'].gender,
                    'Edad': ExcelService._calcular_edad(est_data['estudiante'].birthdate),
                    'Total Asistencias': est_data['presentes'],
                    'Total Sesiones': total_sesiones_mes,
                    'Porcentaje Asistencia (%)': round(porcentaje, 2),
                    'Estatus': estatus
                })
            
            df_mensual = pd.DataFrame(datos_mensuales)
            df_mensual.to_excel(writer, sheet_name='Lista Asistencia Mensual', index=False)
          # 4. ALUMNOS CON ASISTENCIA IRREGULAR (<25%)
        # Optimización: usar las asistencias ya calculadas
        alumnos_irregulares = []
        
        # Obtener todos los estudiantes que han tenido alguna asistencia
        estudiantes_todos = Students.objects.select_related().prefetch_related('attendancestudent_set')
        
        # Obtener conteos de asistencias en una sola consulta
        asistencias_totales = AttendanceStudent.objects.values('id_student').annotate(
            total_presentes=Count('id', filter=Q(attendance='PRESENT')),
            total_registros=Count('id')
        )
        
        # Crear diccionario para acceso rápido
        asistencias_dict = {a['id_student']: a for a in asistencias_totales}
        
        for estudiante in estudiantes_todos:
            if estudiante.id in asistencias_dict:
                data = asistencias_dict[estudiante.id]
                total_registros_est = data['total_registros']
                presentes_est = data['total_presentes']
                
                if total_registros_est > 0:
                    porcentaje = presentes_est / total_registros_est
                    if porcentaje < 0.25:  # Exactamente <25% según requerimientos
                        alumnos_irregulares.append({
                            'ID': estudiante.id,
                            'Nombre': estudiante.name,
                            'Apellido': estudiante.last_name,
                            'Sexo': estudiante.gender,
                            'Edad': ExcelService._calcular_edad(estudiante.birthdate),
                            'Porcentaje Asistencia (%)': round(porcentaje * 100, 2),
                            'Total Presentes': presentes_est,
                            'Total Registros': total_registros_est
                        })
        
        df_irregulares = pd.DataFrame(alumnos_irregulares)
        df_irregulares.to_excel(writer, sheet_name='Alumnos Irregulares', index=False)
          # 5. GRUPOS CON MAYOR O MENOR ASISTENCIA
        if criterio == 'sexo':
            grupos_data = []
            for genero in ['M', 'F']:
                estudiantes_genero = Students.objects.filter(gender=genero)
                total_estudiantes = estudiantes_genero.count()
                
                if total_estudiantes > 0:
                    total_asistencias = AttendanceStudent.objects.filter(
                        id_student__in=estudiantes_genero,
                        attendance='PRESENT'
                    ).count()
                    total_registros = AttendanceStudent.objects.filter(
                        id_student__in=estudiantes_genero
                    ).count()
                    
                    porcentaje = (total_asistencias / total_registros * 100) if total_registros > 0 else 0
                    
                    grupos_data.append({
                        'Sexo': 'Masculino' if genero == 'M' else 'Femenino',
                        'Total Estudiantes': total_estudiantes,
                        'Total Asistencias': total_asistencias,
                        'Total Registros': total_registros,
                        'Porcentaje Asistencia (%)': round(porcentaje, 2)
                    })
            
            df_grupos = pd.DataFrame(grupos_data)
            df_grupos.to_excel(writer, sheet_name='Grupos por Sexo', index=False)
        
        else:  # criterio == 'edad'
            rangos_edad = [
                (0, 8, '0-8 años'),
                (9, 12, '9-12 años'),
                (13, 16, '13-16 años'),
                (17, 100, '17+ años')
            ]
            grupos_data = []
            
            # Optimización: obtener todas las edades de una vez
            estudiantes_con_edad = Students.objects.filter(birthdate__isnull=False).values('id', 'birthdate')
            estudiantes_por_rango = {label: [] for _, _, label in rangos_edad}
            
            today = date.today()
            for est in estudiantes_con_edad:
                edad = today.year - est['birthdate'].year - ((today.month, today.day) < (est['birthdate'].month, est['birthdate'].day))
                for min_edad, max_edad, label in rangos_edad:
                    if min_edad <= edad <= max_edad:
                        estudiantes_por_rango[label].append(est['id'])
                        break
            
            for min_edad, max_edad, label in rangos_edad:
                estudiantes_rango = estudiantes_por_rango[label]
                total_estudiantes = len(estudiantes_rango)
                
                if total_estudiantes > 0:
                    total_asistencias = AttendanceStudent.objects.filter(
                        id_student__in=estudiantes_rango,
                        attendance='PRESENT'
                    ).count()
                    total_registros = AttendanceStudent.objects.filter(
                        id_student__in=estudiantes_rango
                    ).count()
                    
                    porcentaje = (total_asistencias / total_registros * 100) if total_registros > 0 else 0
                    
                    grupos_data.append({
                        'Rango Edad': label,
                        'Total Estudiantes': total_estudiantes,
                        'Total Asistencias': total_asistencias,
                        'Total Registros': total_registros,
                        'Porcentaje Asistencia (%)': round(porcentaje, 2)
                    })
            
            df_grupos = pd.DataFrame(grupos_data)
            df_grupos.to_excel(writer, sheet_name='Grupos por Edad', index=False)
          # 6. LISTA DE ALUMNOS CON MÁS DE 30 FALTAS SEGUIDAS
        # Optimización: una sola consulta para obtener todas las asistencias ordenadas
        asistencias_ordenadas = AttendanceStudent.objects.select_related('id_student').order_by('id_student', 'id_session__date')
        
        # Procesar por estudiante
        alumnos_faltas_seguidas = []
        estudiante_actual = None
        faltas_consecutivas = 0
        max_faltas_consecutivas = 0
        
        for asistencia in asistencias_ordenadas:
            if estudiante_actual != asistencia.id_student:
                # Nuevo estudiante - procesar el anterior si existe
                if estudiante_actual and max_faltas_consecutivas > 30:
                    alumnos_faltas_seguidas.append({
                        'ID': estudiante_actual.id,
                        'Nombre': estudiante_actual.name,
                        'Apellido': estudiante_actual.last_name,
                        'Sexo': estudiante_actual.gender,
                        'Edad': ExcelService._calcular_edad(estudiante_actual.birthdate),
                        'Máximo Faltas Consecutivas': max_faltas_consecutivas,
                        'Estado': 'Requiere Seguimiento'
                    })
                
                # Reiniciar contadores para el nuevo estudiante
                estudiante_actual = asistencia.id_student
                faltas_consecutivas = 0
                max_faltas_consecutivas = 0
            
            # Procesar asistencia actual
            if asistencia.attendance == 'ABSENT':
                faltas_consecutivas += 1
                max_faltas_consecutivas = max(max_faltas_consecutivas, faltas_consecutivas)
            else:
                faltas_consecutivas = 0
        
        # Procesar el último estudiante
        if estudiante_actual and max_faltas_consecutivas > 30:
            alumnos_faltas_seguidas.append({
                'ID': estudiante_actual.id,
                'Nombre': estudiante_actual.name,
                'Apellido': estudiante_actual.last_name,
                'Sexo': estudiante_actual.gender,
                'Edad': ExcelService._calcular_edad(estudiante_actual.birthdate),
                'Máximo Faltas Consecutivas': max_faltas_consecutivas,
                'Estado': 'Requiere Seguimiento'
            })
        
        df_faltas_seguidas = pd.DataFrame(alumnos_faltas_seguidas)
        df_faltas_seguidas.to_excel(writer, sheet_name='Más de 30 Faltas Seguidas', index=False)
        
        # 7. RESUMEN POR CLASES
        estudiantes_por_clase = []
        for clase in Class.objects.all():
            estudiantes_clase = Students.objects.filter(
                attendancestudent__id_session__id_class=clase
            ).distinct()
            
            estudiantes_por_clase.append({
                'ID Clase': clase.id,
                'Nombre Clase': clase.name,
                'Día': clase.day,
                'Hora': f"{clase.start_time} - {clase.end_time}",
                'Total Estudiantes': estudiantes_clase.count(),
                'Total Sesiones': Session.objects.filter(id_class=clase).count()
            })
        
        df_clases_est = pd.DataFrame(estudiantes_por_clase)
        df_clases_est.to_excel(writer, sheet_name='Resumen por Clases', index=False)
        
        # Cerrar el writer y devolver el buffer
        writer.close()
        output.seek(0)
        
        return output