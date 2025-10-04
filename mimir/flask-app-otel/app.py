import time
import random
import logging
import sys
from flask import Flask, Response
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# ----------------
# Flask Setup
# ----------------
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("flask-app")

# ----------------
# OpenTelemetry Metrics Setup
# ----------------
prom_reader = PrometheusMetricReader()
provider = MeterProvider(metric_readers=[prom_reader])
metrics.set_meter_provider(provider)
meter = metrics.get_meter(__name__)

# ----------------
# Metrics Definitions
# ----------------

# Counter for total requests
REQUEST_COUNT = meter.create_counter(
    "flask_request_count_total", description="Total requests"
)

# Histogram for request latency (seconds)
REQUEST_LATENCY = meter.create_histogram(
    "flask_request_latency_seconds", description="Request latency in seconds"
)

# UpDownCounter for in-progress requests
IN_PROGRESS = meter.create_up_down_counter(
    "flask_inprogress_requests", description="Requests in progress"
)

# Observable Gauges for CPU and Memory usage
def cpu_usage_callback(observer):
    observer.observe(random.uniform(5, 95))

def memory_usage_callback(observer):
    observer.observe(random.uniform(50, 500))

CPU_USAGE = meter.create_observable_gauge(
    "flask_cpu_usage_percent", callbacks=[cpu_usage_callback], description="Fake CPU usage %"
)

MEMORY_USAGE = meter.create_observable_gauge(
    "flask_memory_usage_mb", callbacks=[memory_usage_callback], description="Fake memory usage MB"
)

# Summary for /work endpoint (optional, can be used as histogram alternative)
WORK_SUMMARY = meter.create_histogram(
    "flask_work_time_seconds", description="Time taken for /work endpoint"
)

# ----------------
# Routes
# ----------------
@app.route("/")
def home():
    endpoint = "/"
    REQUEST_COUNT.add(1, {"endpoint": endpoint})
    IN_PROGRESS.add(1, {"endpoint": endpoint})
    start = time.time()

    # Simulate CPU + Memory load
    time.sleep(random.uniform(0.1, 0.5))

    duration = time.time() - start
    REQUEST_LATENCY.record(duration, {"endpoint": endpoint})
    logger.info("Home endpoint hit", extra={"latency": duration})
    IN_PROGRESS.add(-1, {"endpoint": endpoint})

    html = """
    <h1>Hello from Flask Metrics Demo (OTel)!</h1>
    <ul>
        <li><a href="/metrics">Metrics</a></li>
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
    start = time.time()

    # Simulate work
    sleep_time = random.uniform(0.2, 1.0)
    time.sleep(sleep_time)
    WORK_SUMMARY.record(sleep_time, {"endpoint": endpoint})

    duration = time.time() - start
    REQUEST_LATENCY.record(duration, {"endpoint": endpoint})
    logger.info("Work endpoint done", extra={"latency": duration})
    IN_PROGRESS.add(-1, {"endpoint": endpoint})

    return f"Work completed in {duration:.2f} seconds"

@app.route("/error")
def error():
    endpoint = "/error"
    REQUEST_COUNT.add(1, {"endpoint": endpoint})
    logger.error("Simulated error triggered", extra={"endpoint": endpoint})
    raise Exception("Simulated failure in /error")

@app.route("/metrics")
def metrics_endpoint():
    # Exposed automatically in Prometheus format
    return prom_reader.render_metrics()

# ----------------
# Main
# ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
