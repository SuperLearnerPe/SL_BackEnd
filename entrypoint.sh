#!/bin/bash
set -e

# Instalar dependencias (por si hay cambios)
pip install --no-cache-dir -r requirements.txt

# Colectar archivos estáticos (opcional si ya se hace en Dockerfile)
python manage.py collectstatic --noinput

# Iniciar el servidor con configuración optimizada para producción
PORT=${PORT:-8000}
exec gunicorn --bind 0.0.0.0:$PORT --workers 3 --timeout 120 SuperLearner_Peru.wsgi:application
