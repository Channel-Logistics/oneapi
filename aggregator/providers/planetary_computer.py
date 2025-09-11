# providers/planetary.py
import httpx
import planetary_computer
from .base import BaseProvider
import logging

logger = logging.getLogger("PlanetaryProvider")

class PlanetaryComputerProvider(BaseProvider):
    name = "PlanetaryComputer"
    stac_url = "https://planetarycomputer.microsoft.com/api/stac/v1/search"

    async def search_archive(self, start_date, end_date, bbox, mode="archive"):
        # Here we explicitly list major collections PC hosts (EO + SAR)
        collections = [
            "sentinel-2-l2a",
            "landsat-8-c2-l2",
            "landsat-9-c2-l2",
            "sentinel-1-grd"
        ]

        payload = {
            "collections": collections,
            "bbox": bbox,
            "datetime": f"{start_date}/{end_date}",
            "limit": 5
        }

        logger.info(f"[PlanetaryComputer] Searching archive with payload={payload}")

        async with httpx.AsyncClient() as client:
            resp = await client.post(self.stac_url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        results = []
        for feat in data.get("features", []):
            signed_assets = {}
            for k, v in feat["assets"].items():
                try:
                    signed_assets[k] = planetary_computer.sign(v["href"])
                except Exception:
                    signed_assets[k] = v["href"]

            results.append(self.format_feature(feat, signed_assets=signed_assets))

        return results
    
    async def search_feasibility(self, *args, **kwargs):
        return []  # Not supported

    async def create_task(self, opportunity, constraints=None):
        return []  # Not supported