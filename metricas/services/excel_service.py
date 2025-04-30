import pandas as pd
import io
from datetime import datetime
from .impacto_service import ImpactoService
from .gestion_service import GestionService

class ExcelService:
    @staticmethod
    def generar_excel_impacto(periodo="mes", umbral_regular=0.5, meses_retencion=6):
        """
        Genera un informe Excel con todas las métricas de impacto:
        1. Tasa de asistencia promedio
        2. Porcentaje y lista de alumnos con asistencia regular
        3. Frecuencia de asistencia
        4. Retención de alumnos
        5. Día de la semana con mayor asistencia
        6. Promedio de sesiones asistidas por alumno
        """
        # Crear un writer de Excel con pandas
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        workbook = writer.book
        
        # Formato para encabezados
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9E1F2',
            'border': 1
        })
        
        # 1. Hoja: Tasa de asistencia (general y por clase)
        # ---------------------------------------------
        tasa_data = ImpactoService.calcular_tasa_asistencia(periodo)
        clases_data = ImpactoService.asistencia_por_clase(periodo)
        
        # Tasa general
        df_tasa = pd.DataFrame([{
            'Periodo': tasa_data['periodo'],
            'Tasa de Asistencia (%)': tasa_data['tasa_asistencia'],
            'Total Asistencias': tasa_data['total_asistencias'],
            'Total Sesiones': tasa_data['total_sesiones']
        }])
        
        sheet_name = 'Tasa de Asistencia'
        df_tasa.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Tasas por clase
        df_clases = pd.DataFrame([
            {
                'ID Clase': item['clase_id'],
                'Nombre': item['clase_nombre'],
                'Día': item['dia'],
                'Tasa Asistencia (%)': item['tasa_asistencia'],
                'Total Asistencias': item['total_asistencias'],
                'Total Sesiones': item['total_sesiones']
            } for item in clases_data
        ])
        
        df_clases.to_excel(writer, sheet_name=sheet_name, startrow=len(df_tasa)+3, index=False)
        worksheet = writer.sheets[sheet_name]
        worksheet.write(len(df_tasa)+2, 0, "Desglose por Clase/Día", header_format)
        
        # 2. Hoja: Alumnos con asistencia regular
        # ---------------------------------------------
        alumnos_data = ImpactoService.alumnos_asistencia_regular(periodo, umbral_regular)
        
        # Datos generales
        df_alumnos_general = pd.DataFrame([{
            'Porcentaje Alumnos Regulares (%)': alumnos_data['porcentaje_alumnos_regulares'],
            'Total Alumnos Regulares': alumnos_data['total_alumnos_regulares'],
            'Total Alumnos': alumnos_data['total_alumnos'],
            'Umbral Considerado (%)': umbral_regular * 100
        }])
        
        sheet_name = 'Alumnos Regulares'
        df_alumnos_general.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Lista detallada de alumnos regulares
        if alumnos_data['alumnos_regulares']:
            df_alumnos_lista = pd.DataFrame([
                {
                    'ID': alumno['id'],
                    'Nombre': alumno['nombre'],
                    'Apellido': alumno['apellido'],
                    'Género': alumno['genero'],
                    'Edad': alumno['edad'],
                    'Porcentaje Asistencia (%)': alumno['porcentaje_asistencia'],
                    'Asistencias': alumno['asistencias'],
                    'Total Sesiones': alumno['total_sesiones']
                } for alumno in alumnos_data['alumnos_regulares']
            ])
            df_alumnos_lista.to_excel(writer, sheet_name=sheet_name, startrow=len(df_alumnos_general)+3, index=False)
            worksheet = writer.sheets[sheet_name]
            worksheet.write(len(df_alumnos_general)+2, 0, "Lista de Alumnos con Asistencia Regular", header_format)
        
        # 3. Hoja: Frecuencia de asistencia
        # ---------------------------------------------
        frecuencia_data = ImpactoService.frecuencia_asistencia(periodo)
        
        # Datos resumen
        df_frecuencia = pd.DataFrame([{
            'Rango 1-3 sesiones': frecuencia_data['rango_1_3'],
            'Rango 4-5 sesiones': frecuencia_data['rango_4_5'],
            'Rango 6+ sesiones': frecuencia_data['rango_6_mas']
        }])
        
        sheet_name = 'Frecuencia Asistencia'
        df_frecuencia.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Distribución detallada
        df_distribucion = pd.DataFrame({
            'Número de Sesiones': list(frecuencia_data['distribucion'].keys()),
            'Cantidad de Alumnos': list(frecuencia_data['distribucion'].values())
        })
        df_distribucion.to_excel(writer, sheet_name=sheet_name, startrow=len(df_frecuencia)+3, index=False)
        worksheet = writer.sheets[sheet_name]
        worksheet.write(len(df_frecuencia)+2, 0, "Distribución Detallada", header_format)
        
        # 4. Hoja: Retención de alumnos
        # ---------------------------------------------
        retencion_data = ImpactoService.retencion_alumnos(meses_retencion)
        
        df_retencion = pd.DataFrame([
            {
                'Mes': item['mes'],
                'Total Alumnos': item['total_alumnos'],
                'Nuevos Alumnos': item['nuevos_alumnos'],
                'Alumnos Retenidos': item['alumnos_retenidos'],
                'Tasa de Retención (%)': item['tasa_retencion']
            } for item in retencion_data
        ])
        
        df_retencion.to_excel(writer, sheet_name='Retención Alumnos', index=False)
        
        # 5. Hoja: Día con mayor asistencia
        # ---------------------------------------------
        dia_data = ImpactoService.dia_mayor_asistencia(periodo)
        
        # Datos resumen
        df_dia = pd.DataFrame([{
            'Día con Mayor Asistencia': dia_data['dia_mayor_asistencia'],
            'Total Asistencias': dia_data['asistencias_por_dia'].get(dia_data['dia_mayor_asistencia'], 0)
        }])
        
        sheet_name = 'Días Asistencia'
        df_dia.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Distribución por día
        df_dias = pd.DataFrame({
            'Día': list(dia_data['asistencias_por_dia'].keys()),
            'Asistencias': list(dia_data['asistencias_por_dia'].values())
        })
        df_dias.to_excel(writer, sheet_name=sheet_name, startrow=len(df_dia)+3, index=False)
        worksheet = writer.sheets[sheet_name]
        worksheet.write(len(df_dia)+2, 0, "Asistencias por Día de la Semana", header_format)
        
        # 6. Hoja: Promedio de sesiones por alumno
        # ---------------------------------------------
        promedio_data = ImpactoService.promedio_sesiones(periodo)
        
        df_promedio = pd.DataFrame([{
            'Promedio Sesiones por Alumno': promedio_data['promedio_sesiones'],
            'Total Asistencias': promedio_data['total_asistencias'],
            'Total Alumnos': promedio_data['total_alumnos']
        }])
        
        df_promedio.to_excel(writer, sheet_name='Promedio Sesiones', index=False)
        
        # Guardar el archivo Excel
        writer.close()
        output.seek(0)
        
        return output

    @staticmethod
    def generar_excel_gestion(fecha=None, fecha_inicio=None, mes=None, anio=None, 
                             clase_id=None, umbral_irregular=0.25, criterio='sexo', 
                             dias_inactivos=30):
        """
        Genera un informe Excel con todas las métricas de gestión:
        1. Lista de asistencia diaria
        2. Lista de asistencia semanal
        3. Lista de asistencia mensual
        4. Alumnos con asistencia irregular
        5. Grupos con mayor/menor asistencia
        6. Lista de alumnos inactivos
        """
        # Preparar fecha actual si es necesario
        now = datetime.now()
        if not fecha:
            fecha = now.date()
        if not fecha_inicio:
            fecha_inicio = now.date().replace(day=1)
        if not mes:
            mes = now.month
        if not anio:
            anio = now.year
        
        # Crear un writer de Excel con pandas
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        workbook = writer.book
        
        # Formato para encabezados
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9E1F2',
            'border': 1
        })
        
        # 1. Hoja: Asistencia diaria
        # ---------------------------------------------
        asistencia_diaria = GestionService.lista_asistencia_diaria(fecha, clase_id)
        
        # Datos generales
        df_diaria_general = pd.DataFrame([{
            'Fecha': asistencia_diaria['fecha'],
            'Clase': asistencia_diaria['clase'] if 'clase' in asistencia_diaria else 'Todas',
            'Total Alumnos': asistencia_diaria['total_alumnos']
        }])
        
        sheet_name = 'Asistencia Diaria'
        df_diaria_general.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Listado de alumnos
        if 'alumnos' in asistencia_diaria and asistencia_diaria['alumnos']:
            df_diaria_alumnos = pd.DataFrame([
                {
                    'ID': alumno['id'],
                    'Nombre': alumno['nombre'],
                    'Apellido': alumno['apellido'],
                    'Género': alumno['genero'],
                    'Edad': alumno['edad'],
                    'Asistencia': alumno['asistencia']
                } for alumno in asistencia_diaria['alumnos']
            ])
            df_diaria_alumnos.to_excel(writer, sheet_name=sheet_name, startrow=len(df_diaria_general)+3, index=False)
            worksheet = writer.sheets[sheet_name]
            worksheet.write(len(df_diaria_general)+2, 0, "Listado de Alumnos", header_format)
        
        # 2. Hoja: Asistencia semanal
        # ---------------------------------------------
        asistencia_semanal = GestionService.lista_asistencia_semanal(fecha_inicio, clase_id)
        
        # Datos generales
        df_semanal_general = pd.DataFrame([{
            'Semana Inicio': asistencia_semanal['semana_inicio'],
            'Semana Fin': asistencia_semanal['semana_fin'],
            'Total Alumnos': asistencia_semanal['total_alumnos'],
            'Total Sesiones': asistencia_semanal['total_sesiones']
        }])
        
        sheet_name = 'Asistencia Semanal'
        df_semanal_general.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Listado de alumnos
        if 'alumnos' in asistencia_semanal and asistencia_semanal['alumnos']:
            df_semanal_alumnos = pd.DataFrame([
                {
                    'ID': alumno['id'],
                    'Nombre': alumno['nombre'],
                    'Apellido': alumno['apellido'],
                    'Género': alumno['genero'],
                    'Edad': alumno['edad'],
                    'Asistencias': alumno['total_asistencias'],
                    'Sesiones': alumno['total_sesiones'],
                    'Porcentaje (%)': alumno['porcentaje_asistencia'],
                    'Estatus': alumno['estatus']
                } for alumno in asistencia_semanal['alumnos']
            ])
            df_semanal_alumnos.to_excel(writer, sheet_name=sheet_name, startrow=len(df_semanal_general)+3, index=False)
            worksheet = writer.sheets[sheet_name]
            worksheet.write(len(df_semanal_general)+2, 0, "Listado de Alumnos", header_format)
        
        # 3. Hoja: Asistencia mensual
        # ---------------------------------------------
        asistencia_mensual = GestionService.lista_asistencia_mensual(mes, anio, clase_id)
        
        # Datos generales
        df_mensual_general = pd.DataFrame([{
            'Mes': asistencia_mensual['mes'],
            'Año': asistencia_mensual['anio'],
            'Total Alumnos': asistencia_mensual['total_alumnos'],
            'Total Sesiones': asistencia_mensual['total_sesiones']
        }])
        
        sheet_name = 'Asistencia Mensual'
        df_mensual_general.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Listado de alumnos
        if 'alumnos' in asistencia_mensual and asistencia_mensual['alumnos']:
            df_mensual_alumnos = pd.DataFrame([
                {
                    'ID': alumno['id'],
                    'Nombre': alumno['nombre'],
                    'Apellido': alumno['apellido'],
                    'Género': alumno['genero'],
                    'Edad': alumno['edad'],
                    'Asistencias': alumno['total_asistencias'],
                    'Sesiones': alumno['total_sesiones'],
                    'Porcentaje (%)': alumno['porcentaje_asistencia'],
                    'Estatus': alumno['estatus']
                } for alumno in asistencia_mensual['alumnos']
            ])
            df_mensual_alumnos.to_excel(writer, sheet_name=sheet_name, startrow=len(df_mensual_general)+3, index=False)
            worksheet = writer.sheets[sheet_name]
            worksheet.write(len(df_mensual_general)+2, 0, "Listado de Alumnos", header_format)
        
        # 4. Hoja: Alumnos con asistencia irregular
        # ---------------------------------------------
        asistencia_irregular = GestionService.alumnos_asistencia_irregular('mes', umbral_irregular)
        
        # Datos generales
        df_irregular_general = pd.DataFrame([{
            'Periodo': asistencia_irregular['periodo'],
            'Umbral (%)': asistencia_irregular['umbral'],
            'Total Alumnos Irregulares': asistencia_irregular['total_alumnos_irregulares'],
            'Porcentaje (%)': asistencia_irregular['porcentaje']
        }])
        
        sheet_name = 'Asistencia Irregular'
        df_irregular_general.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Listado de alumnos
        if 'alumnos' in asistencia_irregular and asistencia_irregular['alumnos']:
            df_irregular_alumnos = pd.DataFrame([
                {
                    'ID': alumno['id'],
                    'Nombre': alumno['nombre'],
                    'Apellido': alumno['apellido'],
                    'Género': alumno['genero'],
                    'Edad': alumno['edad'],
                    'Asistencias': alumno['asistencias'],
                    'Sesiones': alumno['total_sesiones'],
                    'Porcentaje (%)': alumno['porcentaje_asistencia']
                } for alumno in asistencia_irregular['alumnos']
            ])
            df_irregular_alumnos.to_excel(writer, sheet_name=sheet_name, startrow=len(df_irregular_general)+3, index=False)
            worksheet = writer.sheets[sheet_name]
            worksheet.write(len(df_irregular_general)+2, 0, "Listado de Alumnos con Asistencia Irregular", header_format)
        
        # 5. Hoja: Análisis por grupos
        # ---------------------------------------------
        grupos_asistencia = GestionService.analisis_grupos_asistencia(criterio, 'mes')
        
        # Datos generales
        df_grupos_general = pd.DataFrame([{
            'Criterio': grupos_asistencia['criterio'],
            'Periodo': grupos_asistencia['periodo']
        }])
        
        sheet_name = 'Grupos Asistencia'
        df_grupos_general.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Datos por grupo
        grupos_data = []
        for grupo, datos in grupos_asistencia['grupos'].items():
            grupos_data.append({
                'Grupo': grupo,
                'Total Estudiantes': datos['total_estudiantes'],
                'Asistencias': datos['asistencias'],
                'Porcentaje (%)': datos['porcentaje']
            })
        
        df_grupos = pd.DataFrame(grupos_data)
        df_grupos.to_excel(writer, sheet_name=sheet_name, startrow=len(df_grupos_general)+3, index=False)
        worksheet = writer.sheets[sheet_name]
        worksheet.write(len(df_grupos_general)+2, 0, f"Asistencias por {criterio.capitalize()}", header_format)
        
        # 6. Hoja: Alumnos inactivos
        # ---------------------------------------------
        alumnos_inactivos = GestionService.alumnos_inactivos(dias_inactivos)
        
        # Datos generales
        df_inactivos_general = pd.DataFrame([{
            'Días Inactividad Mínimo': alumnos_inactivos['dias_inactividad_limite'],
            'Total Alumnos Inactivos': alumnos_inactivos['total_alumnos_inactivos']
        }])
        
        sheet_name = 'Alumnos Inactivos'
        df_inactivos_general.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Listado de alumnos
        if 'alumnos' in alumnos_inactivos and alumnos_inactivos['alumnos']:
            df_inactivos_alumnos = pd.DataFrame([
                {
                    'ID': alumno['id'],
                    'Nombre': alumno['nombre'],
                    'Apellido': alumno['apellido'],
                    'Género': alumno['genero'],
                    'Edad': alumno['edad'],
                    'Última Asistencia': alumno['ultima_asistencia'],
                    'Días Inactividad': alumno['dias_inactividad'],
                    'Clases': ', '.join(alumno['clases']) if 'clases' in alumno else ''
                } for alumno in alumnos_inactivos['alumnos']
            ])
            df_inactivos_alumnos.to_excel(writer, sheet_name=sheet_name, startrow=len(df_inactivos_general)+3, index=False)
            worksheet = writer.sheets[sheet_name]
            worksheet.write(len(df_inactivos_general)+2, 0, "Alumnos sin Asistir", header_format)
        
        # Guardar el archivo Excel
        writer.close()
        output.seek(0)
        
        return output