FROM python:3.11-slim
WORKDIR /app

# Install local shared contracts package (editable for faster import resolution)
COPY packages/oneapi-contracts /deps/oneapi-contracts
RUN pip install --no-cache-dir -e /deps/oneapi-contracts

# Install gateway deps
COPY gateway/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Install gateway tests deps
COPY gateway/requirements-test.txt ./requirements-test.txt
RUN pip install --no-cache-dir -r requirements-test.txt

COPY gateway/ .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
