FROM python:3.11-slim

WORKDIR /app

COPY app.py /app/

# Install required packages
RUN pip install --no-cache-dir flask \
    opentelemetry-api \
    opentelemetry-sdk \
    opentelemetry-exporter-otlp \
    opentelemetry-instrumentation-flask

EXPOSE 5000

CMD ["python", "app.py"]
