FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port (service1=5000, service2=5001)
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
