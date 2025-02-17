from flask import Flask
import opentracing
from jaeger_client import Config
import random
import time

app = Flask(__name__)

# Jaeger Tracing Setup
def init_tracer(service_name='service2'):
    config = Config(
        config={'sampler': {'type': 'const', 'param': 1}, 'logging': True},
        service_name=service_name,
    )
    return config.initialize_tracer()

tracer = init_tracer()

@app.route('/')
def index():
    span = tracer.start_span('service2-span')
    time.sleep(random.uniform(0.1, 0.5))  # Simulate work
    span.finish()
    return "Service 2 - Hello!"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
