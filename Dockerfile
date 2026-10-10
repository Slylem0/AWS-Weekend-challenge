FROM python:3.12-slim

WORKDIR /app

# System deps kept minimal; all deps are pure-python wheels.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# App Runner sends traffic to this port.
EXPOSE 8080

ENV DRCLOUD_MODEL_ID="us.amazon.nova-pro-v1:0" \
    AWS_REGION="us-east-1"

# FastAPI over plain HTTP: App Runner supports this fully (no WebSockets needed).
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
