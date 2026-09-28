# backend/Dockerfile
FROM python:3.10-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Evitamos que Python genere archivos .pyc y forzamos el autput directo a la consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalamos dependencias del sistema necesarias para compilar asyncpg y bcrypt
RUN apt-get update \
    && apt-get install -y gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiamos solo el archivo de dependencias primero para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código del backend
COPY . .

# Exponemos el puerto que usará Uvicorn
EXPOSE 8000

# Comando por defecto para iniciar el servidor
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]