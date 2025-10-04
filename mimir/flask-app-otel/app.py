import time
import random
import logging
from flask import Flask, Response
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.prometheus import start_http_server

# ----------------
# Flask Setup
# ----------------
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("flask-app")

# ----------------
# OpenTelemetry Metrics Setup
# ----------------
# Start Prometheus-compatible metrics server on port 8000
prom_reader = PrometheusMetricReader()
start_http_server(port=8000)

provider = MeterProvider(metric_readers=[prom_reader])
metrics.set_meter_provider(provider)
meter = metrics.get_meter(__name__)

# ----------------
# Metrics Definitions
# ----------------
REQUEST_COUNT = meter.create_counter("flask_request_count_total", "Total requests")
REQUEST_LATENCY = meter.create_histogram("flask_request_latency_seconds", "Request latency")
IN_PROGRESS = meter.create_up_down_counter("flask_inprogress_requests", "Requests in progress")

def cpu_cb(obs):
    obs.observe(random.uniform(5, 95))
CPU_USAGE = meter.create_observable_gauge("flask_cpu_usage_percent", callbacks=[cpu_cb])

def mem_cb(obs):
    obs.observe(random.uniform(50, 500))
MEMORY_USAGE = meter.create_observable_gauge("flask_memory_usage_mb", callbacks=[mem_cb])

WORK_SUMMARY = meter.create_histogram("flask_work_time_seconds", "Work endpoint duration")

# ----------------
# Flask Routes
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
    <h1>Hello from Flask Metrics Demo (OTel)</h1>
    <ul>
      <li><a href="/work">Work</a></li>
      <li><a href="/error">Error</a></li>
      <li>Metrics exposed on <a href="http://localhost:8000/metrics">http://localhost:8000/metrics</a></li>
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
    logger.info("Starting Flask app on port 5000")
    logger.info("Prometheus metrics exposed on port 8000 at /metrics")
    app.run(host="0.0.0.0", port=5000)
