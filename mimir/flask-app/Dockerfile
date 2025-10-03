FROM python:3.11-slim

WORKDIR /app
COPY app.py /app/
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus

RUN pip install flask prometheus-client

EXPOSE 5000
CMD ["python", "app.py"]
