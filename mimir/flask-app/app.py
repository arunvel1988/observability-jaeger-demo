import time
import random
import logging
import sys
from flask import Flask, Response
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    multiprocess,
)

# ----------------
# Flask Setup
# ----------------
app = Flask(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("flask-app")

# ----------------
# Prometheus Metrics
# ----------------
REQUEST_COUNT = Counter("flask_request_count", "Total requests", ["endpoint"])
REQUEST_LATENCY = Histogram(
    "flask_request_latency_seconds", "Request latency", ["endpoint"]
)
IN_PROGRESS = Gauge("flask_inprogress_requests", "Requests in progress", ["endpoint"])
CPU_USAGE = Gauge("flask_cpu_usage_percent", "Fake CPU usage %")
MEMORY_USAGE = Gauge("flask_memory_usage_mb", "Fake memory usage in MB")
WORK_SUMMARY = Summary("flask_work_time_seconds", "Time taken for /work endpoint")

# ----------------
# Routes
# ----------------
from flask import Response

@app.route("/")
def home():
    endpoint = "/"
    REQUEST_COUNT.labels(endpoint=endpoint).inc()
    IN_PROGRESS.labels(endpoint=endpoint).inc()
    start = time.time()

    # Simulated CPU + Memory load
    sleep_time = random.uniform(0.1, 0.5)
    time.sleep(sleep_time)
    CPU_USAGE.set(random.uniform(5, 95))
    MEMORY_USAGE.set(random.uniform(50, 500))

    duration = time.time() - start
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
    logger.info("Home endpoint hit", extra={"latency": duration})
    IN_PROGRESS.labels(endpoint=endpoint).dec()

    html = """
    <h1>Hello from Flask Metrics Demo!</h1>
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
    REQUEST_COUNT.labels(endpoint=endpoint).inc()
    IN_PROGRESS.labels(endpoint=endpoint).inc()
    start = time.time()

    with WORK_SUMMARY.time():
        sleep_time = random.uniform(0.2, 1.0)
        time.sleep(sleep_time)
        CPU_USAGE.set(random.uniform(10, 90))
        MEMORY_USAGE.set(random.uniform(100, 1000))

    duration = time.time() - start
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
    logger.info("Work endpoint done", extra={"latency": duration})
    IN_PROGRESS.labels(endpoint=endpoint).dec()

    return f"Work completed in {duration:.2f} seconds"

@app.route("/error")
def error():
    endpoint = "/error"
    REQUEST_COUNT.labels(endpoint=endpoint).inc()
    logger.error("Simulated error triggered", extra={"endpoint": endpoint})
    raise Exception("Simulated failure in /error")

@app.route("/metrics")
def metrics():
    # Default metrics + custom
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    data = generate_latest(registry)
    return Response(data, mimetype=CONTENT_TYPE_LATEST)

# ----------------
# Main
# ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
