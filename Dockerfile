# Usar una versión específica de Python para evitar problemas de compatibilidad
FROM python:3.11-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar solo los archivos necesarios primero (para optimizar la caché de Docker)
COPY requirements.txt .

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto 5000
EXPOSE 5000  

# Comando de ejecución (permitiendo recarga automática con Flask)
CMD ["python", "app.py"]
