FROM python:3.11-slim
WORKDIR /app
COPY aggregator/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY aggregator/worker.py .
CMD ["python", "worker.py"]