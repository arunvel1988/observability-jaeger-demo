# flask-app-otel/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY app.py /app/

RUN pip install flask opentelemetry-api opentelemetry-sdk \
    opentelemetry-instrumentation-flask \
    opentelemetry-exporter-otlp

EXPOSE 5000
CMD ["python", "app.py"]
