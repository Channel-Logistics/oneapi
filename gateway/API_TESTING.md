# Gateway API Testing Guide

Quick health checks and basic functionality testing for the Gateway API.

## Prerequisites

1. Install jq:
   ```bash
   # macOS
   brew install jq
   
   # Ubuntu/Debian
   sudo apt-get install jq
   ```

2. Start services:
   ```bash
   make up
   ```

3. Wait for services to be ready (10-15 seconds)

4. Gateway runs on `http://localhost:8000`

## Quick Health Check

### 1. Service Health
```bash
curl -s "http://localhost:8000/health" | jq
```

**Expected Response:**
```json
{
  "ok": true
}
```

### 2. Create Order and Get ID
```bash
# Create order and extract ID
ORDER_ID=$(curl -s -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": [-75.58, 10.37, -75.49, 10.43],
    "start_date": "2024-01-15T10:00:00Z",
    "end_date": "2024-01-15T11:00:00Z"
  }' | jq -r '.orderId')

echo "Created order: $ORDER_ID"
```

### 3. Listen to Events (Optional)
```bash
# Listen to order events
curl -N -H "Accept: text/event-stream" \
  "http://localhost:8000/orders/$ORDER_ID/events"
```

### 4. Create Order and Monitor SSE Channel
```bash
# Create order and monitor SSE channel
echo "Creating order and monitoring SSE channel..."

# Create order
RESPONSE=$(curl -s -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": [-75.58, 10.37, -75.49, 10.43],
    "start_date": "2024-01-15T10:00:00Z",
    "end_date": "2024-01-15T11:00:00Z"
  }')

# Check if order was created successfully
if echo $RESPONSE | jq -e '.orderId' > /dev/null; then
  ORDER_ID=$(echo $RESPONSE | jq -r '.orderId')
  echo "✓ Order created: $ORDER_ID"
  echo "Response:"
  echo $RESPONSE | jq
  
  # Monitor SSE channel (press Ctrl+C to stop)
  echo "Monitoring SSE channel for order: $ORDER_ID"
  echo "Press Ctrl+C to stop monitoring..."
  echo "---"
  curl -N -H "Accept: text/event-stream" \
    "http://localhost:8000/orders/$ORDER_ID/events"
else
  echo "✗ Failed to create order:"
  echo $RESPONSE | jq
fi
```

## Complete Test Script

```bash
#!/bin/bash
# Quick API health check

echo "=== Gateway API Health Check ==="

# 1. Health check
echo "1. Checking service health..."
if curl -s "http://localhost:8000/health" | jq -e '.ok' > /dev/null; then
  echo "✓ Service is healthy"
else
  echo "✗ Service is not responding"
  exit 1
fi

# 2. Create order
echo "2. Creating test order..."
RESPONSE=$(curl -s -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": [-75.58, 10.37, -75.49, 10.43],
    "start_date": "2024-01-15T10:00:00Z",
    "end_date": "2024-01-15T11:00:00Z"
  }')

if echo $RESPONSE | jq -e '.orderId' > /dev/null; then
  ORDER_ID=$(echo $RESPONSE | jq -r '.orderId')
  echo "✓ Order created: $ORDER_ID"
  echo "Response:"
  echo $RESPONSE | jq
else
  echo "✗ Failed to create order:"
  echo $RESPONSE | jq
  exit 1
fi

# 3. Test SSE channel
if [[ "$1" == "--monitor" ]]; then
  echo "3. Monitoring SSE channel..."
  echo "Order ID: $ORDER_ID"
  echo "Press Ctrl+C to stop monitoring..."
  echo "---"
  curl -N -H "Accept: text/event-stream" \
    "http://localhost:8000/orders/$ORDER_ID/events"
else
  echo "3. To monitor events, run: $0 --monitor"
fi

echo "=== Health check completed ==="
```

## Troubleshooting

### Check services
```bash
make ps
```

### Check logs
```bash
make logs-gateway
make logs-storage
```

### Stop services
```bash
make down
```

## Notes

- `bbox` format: `[minLon, minLat, maxLon, maxLat]`
- Dates in ISO 8601 format
- Use `jq -r` for raw string output
- Use `jq -e` to check if field exists
