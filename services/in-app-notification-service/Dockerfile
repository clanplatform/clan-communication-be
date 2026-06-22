FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

FROM base AS builder
COPY services/in-app-notification-service/requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

FROM base AS runtime
COPY --from=builder /install /usr/local
COPY libs/communication_shared /app/libs/communication_shared
COPY services/in-app-notification-service /app
RUN pip install -e /app/libs/communication_shared
EXPOSE 8004
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
