#!/bin/bash
set -e

# Instalar dependencias (por si hay cambios)
pip install --no-cache-dir -r requirements.txt

# Ejecutar migraciones
python manage.py migrate

# Colectar archivos estáticos (opcional si ya se hace en Dockerfile)
python manage.py collectstatic --noinput

# Iniciar el servidor con configuración optimizada para producción
exec gunicorn --bind 0.0.0.0:$PORT --workers 3 --timeout 120 SuperLearner_Peru.wsgi:application
