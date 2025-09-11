# providers/umbra.py
import httpx
import logging
from .base import BaseProvider
import asyncio

logger = logging.getLogger("UmbraProvider")

class UmbraProvider(BaseProvider):
    name = "Umbra"
    # base_url = "https://api.canopy.umbra.space"
    base_url = "https://api.canopy.prod.umbra-sandbox.space"

    def __init__(self, token: str):
        if not token:
            raise ValueError("Umbra token not provided")
        self.token = token
        self.headers = {"Authorization": f"Bearer {self.token}"}

    async def search_archive(self, start_date, end_date, bbox, limit=10):
        """Search Umbra archive (STAC API)"""
        url = f"{self.base_url}/v2/stac/search"
        payload = {
            "collections": ["umbra:imagery"],
            "bbox": bbox,
            "datetime": f"{start_date}/{end_date}",
            "limit": limit,
        }

        logger.info(f"[Umbra] Searching archive bbox={bbox}")

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=self.headers, json=payload, timeout=60)
            resp.raise_for_status()
            return resp.json().get("features", [])

    async def search_feasibility(self, start_date, end_date, geometry):
        """Request feasibility opportunities for new tasking"""
        url = f"{self.base_url}/tasking/feasibilities"
        payload = {
            "imagingMode": "SPOTLIGHT",
            "spotlightConstraints": {
                "geometry": geometry,
                "polarization": "VV",
                "rangeResolutionMinMeters": 1,
                "multilookFactor": 1,
                "grazingAngleMinDegrees": 30,
                "grazingAngleMaxDegrees": 70,
                "targetAzimuthAngleStartDegrees": 0,
                "targetAzimuthAngleEndDegrees": 360
            },
            "windowStartAt": start_date,
            "windowEndAt": end_date,
        }

        logger.info(f"[Umbra] Checking feasibility for {geometry}")

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=self.headers, json=payload, timeout=60)
            resp.raise_for_status()
            feas = resp.json()
        
        feas_id = feas["id"]

        # Poll until completed
        poll_url = f"{self.base_url}/tasking/feasibilities/{feas_id}"
        for _ in range(30):  # up to ~5 minutes if 10s interval
            async with httpx.AsyncClient() as client:
                poll = await client.get(poll_url, headers=self.headers, timeout=60)
                poll.raise_for_status()
                status = poll.json()

            if status["status"] == "COMPLETED":
                logger.info(f"[Umbra] Feasibility {feas_id} completed")
                return status.get("opportunities", [])

            if status["status"] in ("FAILED", "CANCELLED"):
                raise RuntimeError(f"Feasibility {feas_id} failed: {status}")

            await asyncio.sleep(10)

        raise TimeoutError(f"Feasibility {feas_id} polling timed out")

    async def create_task(self, start_date, end_date, geometry, task_name="Sandbox-Test-Task"):
        """
        Create a task from a chosen feasibility opportunity.
        """
        url = f"{self.base_url}/tasking/tasks"

        payload = {
            "imagingMode": "SPOTLIGHT",
            "spotlightConstraints": {
                "geometry": geometry,
                "polarization": "VV",
                "rangeResolutionMinMeters": 1,
                "multilookFactor": 1,
                "grazingAngleMinDegrees": 30,
                "grazingAngleMaxDegrees": 70,
                "targetAzimuthAngleStartDegrees": 0,
                "targetAzimuthAngleEndDegrees": 360
            },
            "windowStartAt": start_date,
            "windowEndAt": end_date,
            "taskName": task_name,
        }

        logger.info(f"[Umbra] Creating task with payload {payload}")

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=self.headers, json=payload, timeout=60)
            resp.raise_for_status()
            return resp.json()

    async def get_task_status(self, task_id: str):
        url = f"{self.base_url}/tasking/tasks/{task_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self.headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data.get("properties", {}).get("status", "UNKNOWN")