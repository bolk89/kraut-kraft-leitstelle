FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir "mistralai>=1.0.0" "mistralai-workflows>=0.1.0" "httpx>=0.27.0"

COPY src ./src
ENV PYTHONPATH=/app

CMD ["python", "-m", "src.entrypoints.worker"]
