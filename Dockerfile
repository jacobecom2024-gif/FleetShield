FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app
COPY requirements-cloud.txt ./requirements-cloud.txt
RUN pip install --no-cache-dir -r requirements-cloud.txt
COPY app ./app

RUN useradd --create-home --uid 10001 fleetshield
USER fleetshield

EXPOSE 8080
CMD ["python", "-m", "app.api"]
