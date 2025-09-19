import httpx
from contracts import OrderCreate
from fastapi import HTTPException


class StorageClient:
    def __init__(self, base_url: str, timeout_seconds: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=timeout_seconds)

    async def create_order(self, order: OrderCreate) -> dict:
        payload = order.model_dump(mode="json")
        try:
            resp = await self.client.post(f"{self.base_url}/orders", json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Storage service error: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Storage unavailable: {e}")

    async def close(self):
        await self.client.aclose()
