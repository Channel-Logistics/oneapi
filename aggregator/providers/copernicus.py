import logging
import os

import httpx
from dotenv import load_dotenv
from logging_config import setup_logging

from .base import BaseProvider

load_dotenv()
setup_logging()
logger = logging.getLogger("Copernicus")


class CopernicusProvider(BaseProvider):
    name = "Copernicus"
    stac_url = os.getenv("COPERNICUS_URL")

    async def search_archive(self, start_date, end_date, bbox):
        payload = {"bbox": bbox, "datetime": f"{start_date}/{end_date}", "limit": 5}

        logger.info(f"[Copernicus] Searching archive with payload={payload}")

        async with httpx.AsyncClient() as client:
            resp = await client.post(self.stac_url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        return [self.format_feature(feat) for feat in data.get("features", [])]

    async def search_feasibility(self, *args, **kwargs):
        return []  # Not supported

    async def create_task(self, opportunity, constraints=None):
        return []  # Not supported
