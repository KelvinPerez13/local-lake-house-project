FROM python:3.11.11-slim-bookworm
WORKDIR /app
COPY requirements /app/requirements
RUN pip install --no-cache-dir -r requirements/ingestion.txt
COPY pipelines /app/pipelines
COPY tests /app/tests
ENV PYTHONPATH=/app PYTHONUNBUFFERED=1
