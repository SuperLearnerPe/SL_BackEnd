from rest_framework import serializers

class AlumnoAsistenciaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    apellido = serializers.CharField()
    genero = serializers.CharField()
    edad = serializers.IntegerField(allow_null=True)
    asistencia = serializers.CharField()

class AsistenciaDiariaSerializer(serializers.Serializer):
    fecha = serializers.DateField()
    clase = serializers.CharField()
    total_alumnos = serializers.IntegerField()
    alumnos = AlumnoAsistenciaSerializer(many=True)

class AlumnoAsistenciaSemanalSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    apellido = serializers.CharField()
    genero = serializers.CharField()
    edad = serializers.IntegerField(allow_null=True)
    total_asistencias = serializers.IntegerField()
    total_sesiones = serializers.IntegerField()
    porcentaje_asistencia = serializers.FloatField()
    estatus = serializers.CharField()  # 'regular', 'baja asistencia', 'ausente'

class AsistenciaSemanalSerializer(serializers.Serializer):
    semana_inicio = serializers.DateField()
    semana_fin = serializers.DateField()
    total_alumnos = serializers.IntegerField()
    total_sesiones = serializers.IntegerField()
    alumnos = AlumnoAsistenciaSemanalSerializer(many=True)

class AlumnoAsistenciaMensualSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    apellido = serializers.CharField()
    genero = serializers.CharField()
    edad = serializers.IntegerField(allow_null=True)
    total_asistencias = serializers.IntegerField()
    total_sesiones = serializers.IntegerField()
    porcentaje_asistencia = serializers.FloatField()
    estatus = serializers.CharField()  # 'regular', 'baja asistencia', 'ausente'

class AsistenciaMensualSerializer(serializers.Serializer):
    mes = serializers.CharField()
    anio = serializers.IntegerField()
    total_alumnos = serializers.IntegerField()
    total_sesiones = serializers.IntegerField()
    alumnos = AlumnoAsistenciaMensualSerializer(many=True)

class AlumnosIrregularesSerializer(serializers.Serializer):
    total_alumnos = serializers.IntegerField()
    total_irregulares = serializers.IntegerField()
    porcentaje_irregulares = serializers.FloatField()
    alumnos = AlumnoAsistenciaSemanalSerializer(many=True)

class GrupoAsistenciaSerializer(serializers.Serializer):
    grupo = serializers.CharField()
    total_alumnos = serializers.IntegerField()
    total_asistencias = serializers.IntegerField()
    promedio_asistencia = serializers.FloatField()

class GruposAsistenciaSerializer(serializers.Serializer):
    criterio = serializers.CharField()  # 'sexo', 'edad'
    grupos = GrupoAsistenciaSerializer(many=True)

class AlumnoInactivoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    apellido = serializers.CharField()
    dias_inactivo = serializers.IntegerField()
    ultima_asistencia = serializers.DateField(allow_null=True)
    contacto_info = serializers.DictField()

class AlumnosInactivosSerializer(serializers.Serializer):
    total_alumnos_inactivos = serializers.IntegerField()
    dias_inactividad = serializers.IntegerField()
    alumnos = AlumnoInactivoSerializer(many=True)