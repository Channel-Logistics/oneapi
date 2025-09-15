FROM python:3.11-slim

WORKDIR /app

COPY storage/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# DTOs contracts
COPY packages/oneapi-contracts /app/packages/oneapi-contracts
RUN pip install -e /app/packages/oneapi-contracts

COPY storage /app/storage

COPY storage/alembic.ini ./alembic.ini
COPY storage/migrations ./migrations

ENV PYTHONUNBUFFERED=1

EXPOSE 9000

CMD ["uvicorn", "storage.main:app", "--host", "0.0.0.0", "--port", "9000", "--reload"]