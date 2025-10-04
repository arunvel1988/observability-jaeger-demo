import time
import random
import logging
from flask import Flask, Response
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# ----------------
# Flask Setup
# ----------------
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("flask-app")

# ----------------
# OpenTelemetry Metrics (Alloy)
# ----------------
resource = Resource(attributes={"service.name": "flask-app"})
# OTLP exporter directly pointing to Alloy
otlp_exporter = OTLPMetricExporter(endpoint="http://alloy:4317", insecure=True)
reader = PeriodicExportingMetricReader(otlp_exporter, export_interval_millis=5000)
provider = MeterProvider(metric_readers=[reader], resource=resource)
metrics.set_meter_provider(provider)
meter = metrics.get_meter(__name__)

# Counter for total requests
REQUEST_COUNT = meter.create_counter("flask_request_count_total", "Total requests")
# Histogram for request latency
REQUEST_LATENCY = meter.create_histogram("flask_request_latency_seconds", "Request latency")
# UpDownCounter for in-progress requests
IN_PROGRESS = meter.create_up_down_counter("flask_inprogress_requests", "Requests in progress")

# Observable gauges
def cpu_cb(obs):
    obs.observe(random.uniform(5, 95))
CPU_USAGE = meter.create_observable_gauge("flask_cpu_usage_percent", callbacks=[cpu_cb])

def mem_cb(obs):
    obs.observe(random.uniform(50, 500))
MEMORY_USAGE = meter.create_observable_gauge("flask_memory_usage_mb", callbacks=[mem_cb])

WORK_SUMMARY = meter.create_histogram("flask_work_time_seconds", "Work endpoint duration")

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

    html = """
    <h1>Hello from Flask Metrics Demo (Alloy)</h1>
    <ul>
      <li><a href="/work">Work</a></li>
      <li><a href="/error">Error</a></li>
    </ul>
    """
    return Response(html, mimetype="text/html")

@app.route("/work")
def work():
    endpoint = "/work"
    REQUEST_COUNT.add(1, {"endpoint": endpoint})
    IN_PROGRESS.add(1, {"endpoint": endpoint})
    sleep_time = random.uniform(0.2, 1.0)
    time.sleep(sleep_time)
    WORK_SUMMARY.record(sleep_time, {"endpoint": endpoint})
    REQUEST_LATENCY.record(sleep_time, {"endpoint": endpoint})
    IN_PROGRESS.add(-1, {"endpoint": endpoint})
    return f"Work completed in {sleep_time:.2f} seconds"

@app.route("/error")
def error():
    REQUEST_COUNT.add(1, {"endpoint": "/error"})
    raise Exception("Simulated failure")

# ----------------
# Main
# ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
