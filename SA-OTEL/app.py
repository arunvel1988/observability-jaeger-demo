from flask import Flask
import random
import time
import os
import requests

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Logs
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

# Metrics
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.prometheus import PrometheusMetricReader

app = Flask(__name__)

# --------------------------
# 1️⃣ Tracing Setup
# --------------------------
trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create({SERVICE_NAME: "service1"})
    )
)
tracer = trace.get_tracer(__name__)

# OTLP exporter to Tempo
trace_exporter = OTLPSpanExporter(endpoint="http://tempo:4318/v1/traces")
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(trace_exporter))

# Auto-instrument Flask and Requests
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# --------------------------
# 2️⃣ Metrics Setup (Prometheus)
# --------------------------
meter_provider = MeterProvider(
    metric_readers=[PrometheusMetricReader()]
)
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter("service1-metrics")

request_counter = meter.create_counter(
    name="http_requests_total",
    description="Total HTTP requests"
)

# --------------------------
# 3️⃣ Logging Setup
# --------------------------
logger_provider = LoggerProvider(
    resource=Resource.create({SERVICE_NAME: "service1"})
)
log_exporter = OTLPLogExporter(endpoint="http://tempo:4318/v1/logs")
logger_provider.add_log_processor(BatchLogProcessor(log_exporter))
logger = logger_provider.get_logger("service1-logs")

# --------------------------
# Routes
# --------------------------
@app.route("/")
def index():
    # Metrics
    request_counter.add(1, {"endpoint": "/"})
    # Logs
    logger.emit({"body": "Index endpoint called"})
    # Traces
    with tracer.start_as_current_span("index-span"):
        time.sleep(random.uniform(0.1, 0.5))
        return "Service 1 - Hello!"

@app.route("/call_service2")
def call_service2():
    request_counter.add(1, {"endpoint": "/call_service2"})
    logger.emit({"body": "Calling service2"})
    with tracer.start_as_current_span("call-service2"):
        response = requests.get("http://service2:5001/")
        logger.emit({"body": f"Response from service2: {response.text}"})
        return f"Service 1 called Service 2, Response: {response.text}"

# --------------------------
# Run Flask App
# --------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
