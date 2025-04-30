#!/bin/bash

# Establecer el puerto por defecto
PORT=8000

# Comprobar si se ha proporcionado un argumento para el puerto
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --port) PORT="$2"; shift ;;
        *) echo "Opción desconocida: $1" ;;
    esac
    shift
done

# Realizar migraciones
echo "Realizando migraciones..."
python manage.py migrate

# Iniciar el servidor de desarrollo
echo "Iniciando el servidor en el puerto $PORT..."
python manage.py runserver "0.0.0.0:$PORT"