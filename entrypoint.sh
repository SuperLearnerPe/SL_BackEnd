#!/bin/bash
set -e

# Ejecutar migraciones
python manage.py migrate

# Colectar archivos estáticos (opcional si ya se hace en Dockerfile)
# python manage.py collectstatic --noinput

# Iniciar el servidor
exec gunicorn --bind 0.0.0.0:$PORT SuperLearner_Peru.wsgi:application
