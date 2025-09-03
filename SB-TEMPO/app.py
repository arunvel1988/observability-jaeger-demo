from flask import Flask
import random
import time

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

app = Flask(__name__)

# Setup OTel Tracer for Tempo
trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create({SERVICE_NAME: "service2"})
    )
)
tracer = trace.get_tracer(__name__)

# Configure OTLP Exporter to Tempo (default Tempo listens on 4318 for HTTP)
otlp_exporter = OTLPSpanExporter(endpoint="http://tempo:4318/v1/traces")

span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Auto-instrument Flask
FlaskInstrumentor().instrument_app(app)

@app.route("/")
def index():
    with tracer.start_as_current_span("service2-span"):
        time.sleep(random.uniform(0.1, 0.5))  # Simulate work
        return "Service 2 - Hello!"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
