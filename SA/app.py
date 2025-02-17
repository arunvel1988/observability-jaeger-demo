from flask import Flask
import requests
import opentracing
from jaeger_client import Config
import random
import time

app = Flask(__name__)

# Jaeger Tracing Setup
def init_tracer(service_name='service1'):
    config = Config(
        config={'sampler': {'type': 'const', 'param': 1}, 'logging': True},
        service_name=service_name,
    )
    return config.initialize_tracer()

tracer = init_tracer()

@app.route('/')
def index():
    span = tracer.start_span('index-span')
    time.sleep(random.uniform(0.1, 0.5))  # Simulate work
    span.finish()
    return "Service 1 - Hello!"

@app.route('/call_service2')
def call_service2():
    span = tracer.start_span('call-service2')
    response = requests.get('http://service2:5001/')
    span.finish()
    return f"Service 1 called Service 2, Response: {response.text}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
