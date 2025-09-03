FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt
EXPOSE 5001
CMD ["python", "app.py"]
