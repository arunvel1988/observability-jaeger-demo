# Use official Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy application code
COPY app.py /app/

# Install required Python packages
RUN pip install --no-cache-dir \
    flask \
    opentelemetry-api \
    opentelemetry-sdk \
    opentelemetry-instrumentation-flask \
    opentelemetry-exporter-prometheus

# Expose Flask port
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
