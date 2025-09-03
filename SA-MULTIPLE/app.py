from flask import Flask
import random
import time
import os

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

app = Flask(__name__)

# Dynamic backend selection via environment variable
backend = os.getenv("OTEL_BACKEND", "tempo")  # tempo, jaeger, dynatrace

# Setup OTel Tracer
trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create({SERVICE_NAME: "service1"})
    )
)
tracer = trace.get_tracer(__name__)

# Configure exporter based on backend
if backend == "tempo":
    exporter = OTLPSpanExporter(endpoint="http://tempo:4318/v1/traces")
elif backend == "jaeger":
    exporter = JaegerExporter(agent_host_name="jaeger", agent_port=6831)
elif backend == "dynatrace":
    exporter = OTLPSpanExporter(
        endpoint="https://<YOUR_DYNATRACE_TENANT>/api/v2/otlp/v1/traces",
        headers=(("Authorization", "Api-Token <YOUR_TOKEN>"),)
    )
else:
    raise ValueError(f"Unknown OTEL_BACKEND: {backend}")

span_processor = BatchSpanProcessor(exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Auto-instrument Flask and requests
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

@app.route("/")
def index():
    with tracer.start_as_current_span("index-span"):
        time.sleep(random.uniform(0.1, 0.5))
        return "Service 1 - Hello!"

@app.route("/call_service2")
def call_service2():
    with tracer.start_as_current_span("call-service2"):
        import requests
        response = requests.get("http://service2:5001/")
        return f"Service 1 called Service 2, Response: {response.text}"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
