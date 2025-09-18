#!/usr/bin/env python3
"""
Example script demonstrating the new storage integration in the gateway.

This script shows how to create an order via the gateway that will:
1. Create an order in the storage service
2. Publish the order ID to RabbitMQ along with the request data
"""

import asyncio

import httpx


async def create_order():
    """Example of creating an order"""

    # Gateway URL (adjust if running locally vs in Docker)
    gateway_url = "http://localhost:8000"

    # Example order data
    payload = {
        "bbox": [-122.4, 37.7, -122.3, 37.8],  # San Francisco area
        "start_date": "2024-01-01T00:00:00Z",
        "end_date": "2024-01-02T00:00:00Z",
        "provider": "copernicus",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{gateway_url}/orders", json=payload, timeout=30.0
            )
            response.raise_for_status()

            result = response.json()
            print("Order created successfully!")
            print(f"Order ID: {result['orderId']}")
            print(f"SSE URL: {result['sseUrl']}")

            return result

        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        except httpx.RequestError as e:
            print(f"Request error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


async def create_order_missing_fields():
    """Example of missing fields (should return 400)"""

    gateway_url = "http://localhost:8000"

    payload = {"provider": "test_provider"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{gateway_url}/orders", json=payload, timeout=30.0
            )
            response.raise_for_status()

            print("Unexpected success")

        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        except httpx.RequestError as e:
            print(f"Request error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


async def main():
    """Run examples"""
    print("=== Gateway Storage Integration Example ===\n")

    print("1. Creating order:")
    await create_order()

    print("\n" + "=" * 50 + "\n")

    print("2. Creating order with missing fields:")
    await create_order_missing_fields()


if __name__ == "__main__":
    asyncio.run(main())
