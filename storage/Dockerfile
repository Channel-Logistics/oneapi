FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# DTOs contracts
COPY ../packages/oneapi-contracts /app/packages/oneapi-contracts
RUN pip install -e /app/packages/oneapi-contracts

COPY alembic.ini ./alembic.ini
COPY migrations ./migrations

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
