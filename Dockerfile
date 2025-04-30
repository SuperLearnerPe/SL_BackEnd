FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para mysqlclient
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar solo los requisitos primero para aprovechar el caché de capas
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto
COPY . .

# Configurar variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=SuperLearner_Peru.settings



# Crear directorio para archivos estáticos
RUN mkdir -p /app/staticfiles

# Recolectar archivos estáticos
RUN python manage.py collectstatic --noinput

# Puerto que expondrá el contenedor
EXPOSE 8000

# Ejecutar migraciones y luego iniciar el servidor Gunicorn
CMD python manage.py migrate && \
    gunicorn --bind 0.0.0.0:8000 SuperLearner_Peru.wsgi:application