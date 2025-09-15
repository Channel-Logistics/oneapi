FROM python:3.11-slim

WORKDIR /app

COPY notifications/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY notifications/notifier.py ./notifier.py

CMD ["python", "notifier.py"]
