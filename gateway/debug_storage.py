#!/usr/bin/env python3
import asyncio
import httpx

async def test_storage_connection():
    try:
        async with httpx.AsyncClient() as client:
            # Test health endpoint
            resp = await client.get('http://storage:9000/health')
            print(f"Health check: {resp.status_code} - {resp.text}")
            
            # Test orders endpoint
            order_data = {
                "bbox": [-75.58, 10.37, -75.49, 10.43],
                "start_date": "2024-01-15T10:00:00Z",
                "end_date": "2024-01-15T11:00:00Z"
            }
            resp = await client.post('http://storage:9000/orders', json=order_data)
            print(f"Create order: {resp.status_code} - {resp.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_storage_connection())
