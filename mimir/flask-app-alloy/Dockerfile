# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (Flask + OpenTelemetry)
RUN pip install --no-cache-dir \
    flask \
    opentelemetry-sdk \
    opentelemetry-api \
    opentelemetry-exporter-otlp-proto-grpc \
    opentelemetry-instrumentation-flask

# Copy application code
COPY app.py .

# Expose Flask port
EXPOSE 5000

# Run Flask app
CMD ["python", "app.py"]
