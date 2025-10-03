FROM python:3.11-slim

WORKDIR /app
COPY app.py /app/

# Create the Prometheus multiproc directory and ensure it exists at runtime
RUN mkdir -p /tmp/prometheus && chmod 777 /tmp/prometheus
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus

RUN pip install flask prometheus-client

EXPOSE 5000
CMD ["python", "app.py"]
