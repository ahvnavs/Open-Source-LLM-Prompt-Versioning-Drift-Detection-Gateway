# Use a highly optimized, slim Python base image
FROM python:3.11-slim

# Enforce security by running as a non-root user
RUN useradd -m -r gatewayuser

# Set the working directory
WORKDIR /usr/src/app

# Copy dependency file and install (leverage Docker layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the stateless application code
COPY ./app ./app

# Change ownership to the non-root user
RUN chown -R gatewayuser:gatewayuser /usr/src/app
USER gatewayuser

# 12-Factor App: Port binding (Explicitly expose 8080)
EXPOSE 8080

# Execute the ultra-fast Uvicorn ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
