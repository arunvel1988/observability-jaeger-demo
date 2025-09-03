from flask import Flask
import random
import time

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# Logs
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

# Metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader

app = Flask(__name__)

# --------------------------
# 1️⃣ Tracing Setup
# --------------------------
trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create({SERVICE_NAME: "service2"})
    )
)
tracer = trace.get_tracer(__name__)

# Export traces to OTel Collector (then → Tempo)
trace_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4318/v1/traces")
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(trace_exporter))

# Auto-instrument Flask
FlaskInstrumentor().instrument_app(app)

# --------------------------
# 2️⃣ Metrics Setup (Prometheus)
# --------------------------
meter_provider = MeterProvider(
    metric_readers=[PrometheusMetricReader()]
)
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter("service2-metrics")

request_counter = meter.create_counter(
    name="http_requests_total",
    description="Total HTTP requests"
)

# --------------------------
# 3️⃣ Logging Setup
# --------------------------
logger_provider = LoggerProvider(
    resource=Resource.create({SERVICE_NAME: "service2"})
)

# Export logs to OTel Collector (then → Loki)
log_exporter = OTLPLogExporter(endpoint="http://otel-collector:4318/v1/logs")
logger_provider.add_log_processor(BatchLogRecordProcessor(log_exporter))

logger = logger_provider.get_logger("service2-logs")

# --------------------------
# Routes
# --------------------------
@app.route("/")
def index():
    request_counter.add(1, {"endpoint": "/"})
    logger.info("Service2 index endpoint called")
    with tracer.start_as_current_span("service2-span"):
        time.sleep(random.uniform(0.1, 0.5))
        return "Service 2 - Hello!"

# --------------------------
# Run Flask App
# --------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
