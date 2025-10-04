import time
import random
import logging
from flask import Flask

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# ----------------
# Logging Setup
# ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("flask-app")

# ----------------
# Flask App
# ----------------
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

# ----------------
# OpenTelemetry Metrics Setup
# ----------------
resource = Resource(attributes={"service.name": "flask-app"})
otlp_exporter = OTLPMetricExporter(endpoint="http://otel-collector:4317", insecure=True)
reader = PeriodicExportingMetricReader(otlp_exporter, export_interval_millis=5000)
provider = MeterProvider(metric_readers=[reader], resource=resource)
metrics.set_meter_provider(provider)
meter = metrics.get_meter("flask_app_meter")

# ----------------
# Metrics Definitions
# ----------------
REQUEST_COUNT = meter.create_counter(
    name="flask_request_count_total",
    description="Total requests received",
)
REQUEST_LATENCY = meter.create_histogram(
    name="flask_request_latency_seconds",
    description="Request latency in seconds",
)
IN_PROGRESS = meter.create_up_down_counter(
    name="flask_inprogress_requests",
    description="Requests currently in progress",
)

def cpu_cb(observer):
    observer.observe(random.uniform(5, 95))
CPU_USAGE = meter.create_observable_gauge(
    "flask_cpu_usage_percent", callbacks=[cpu_cb], description="Fake CPU usage %"
)

def mem_cb(observer):
    observer.observe(random.uniform(50, 500))
MEMORY_USAGE = meter.create_observable_gauge(
    "flask_memory_usage_mb", callbacks=[mem_cb], description="Fake memory usage MB"
)

# ----------------
# Routes
# ----------------
@app.route("/")
def home():
    endpoint = "/"
    REQUEST_COUNT.add(1, {"endpoint": endpoint})
    IN_PROGRESS.add(1, {"endpoint": endpoint})

    duration = random.uniform(0.1, 0.5)
    time.sleep(duration)

    REQUEST_LATENCY.record(duration, {"endpoint": endpoint})
    IN_PROGRESS.add(-1, {"endpoint": endpoint})

    return """
    <h1>Hello from Flask App (OTel)</h1>
    <ul>
        <li><a href="/work">Work</a></li>
        <li><a href="/error">Error</a></li>
    </ul>
    """

@app.route("/work")
def work():
    endpoint = "/work"
    REQUEST_COUNT.add(1, {"endpoint": endpoint})
    IN_PROGRESS.add(1, {"endpoint": endpoint})

    sleep_time = random.uniform(0.2, 1.0)
    time.sleep(sleep_time)

    REQUEST_LATENCY.record(sleep_time, {"endpoint": endpoint})
    IN_PROGRESS.add(-1, {"endpoint": endpoint})

    return f"Work completed in {sleep_time:.2f} seconds"

@app.route("/error")
def error():
    REQUEST_COUNT.add(1, {"endpoint": "/error"})
    raise Exception("Simulated error")

# ----------------
# Run App
# ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
