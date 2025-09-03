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

app = Flask(__name__)

# Dynamic backend selection via environment variable
backend = os.getenv("OTEL_BACKEND", "tempo")  # tempo, jaeger, dynatrace

# Setup OTel Tracer
trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create({SERVICE_NAME: "service2"})
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

# Auto-instrument Flask
FlaskInstrumentor().instrument_app(app)

@app.route("/")
def index():
    with tracer.start_as_current_span("service2-span"):
        time.sleep(random.uniform(0.1, 0.5))
        return "Service 2 - Hello!"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
