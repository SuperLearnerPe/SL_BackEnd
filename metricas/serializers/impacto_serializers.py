from rest_framework import serializers

class TasaAsistenciaSerializer(serializers.Serializer):
    periodo = serializers.CharField()  # 'semana', 'mes', 'año'
    tasa_asistencia = serializers.FloatField()
    total_asistencias = serializers.IntegerField()
    total_sesiones = serializers.IntegerField()

class AsistenciaPorClaseSerializer(serializers.Serializer):
    clase_id = serializers.IntegerField()
    clase_nombre = serializers.CharField()
    dia = serializers.CharField()
    tasa_asistencia = serializers.FloatField()
    total_asistencias = serializers.IntegerField()
    total_sesiones = serializers.IntegerField()

class AlumnoAsistenciaRegularSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    apellido = serializers.CharField()
    porcentaje_asistencia = serializers.FloatField()
    total_asistencias = serializers.IntegerField()
    total_sesiones = serializers.IntegerField()

class AlumnosAsistenciaRegularResumenSerializer(serializers.Serializer):
    porcentaje_alumnos_regulares = serializers.FloatField()
    total_alumnos_regulares = serializers.IntegerField()
    total_alumnos = serializers.IntegerField()
    alumnos_regulares = AlumnoAsistenciaRegularSerializer(many=True)

class FrecuenciaAsistenciaSerializer(serializers.Serializer):
    rango_1_3 = serializers.IntegerField()
    rango_4_5 = serializers.IntegerField()
    rango_6_mas = serializers.IntegerField()
    distribucion = serializers.DictField(child=serializers.IntegerField())

class RetencionAlumnosSerializer(serializers.Serializer):
    mes = serializers.CharField()
    total_alumnos = serializers.IntegerField()
    nuevos_alumnos = serializers.IntegerField()
    alumnos_retenidos = serializers.IntegerField()
    tasa_retencion = serializers.FloatField()

class DiaMayorAsistenciaSerializer(serializers.Serializer):
    dia_mayor_asistencia = serializers.CharField()
    asistencias_por_dia = serializers.DictField(child=serializers.IntegerField())

class PromedioSesionesSerializer(serializers.Serializer):
    promedio_sesiones = serializers.FloatField()
    total_asistencias = serializers.IntegerField()
    total_alumnos = serializers.IntegerField()