# app/providers/base.py
import abc
from typing import List, Dict, Any

class BaseProvider(abc.ABC):
    name: str

    @abc.abstractmethod
    async def search_archive(self, start_date: str, end_date: str, bbox: List[float]) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abc.abstractmethod
    async def search_feasibility(self, start_date: str, end_date: str, geometry: Dict[str, Any]) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abc.abstractmethod
    async def create_task(self, opportunity: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a new collection task based on feasibility opportunity."""
        raise NotImplementedError

    def format_feature(self, feat, signed_assets=None):
        """Normalize a STAC feature into a common format"""
        props = feat.get("properties", {})

        assets = signed_assets or {
            k: v.get("href") for k, v in feat.get("assets", {}).items()
        }

        return {
            "id": feat.get("id"),
            "datetime": props.get("datetime"),
            "bbox": feat.get("bbox"),
            "assets": assets,
            "metadata": {
                "cloud_cover": props.get("eo:cloud_cover"),
                "platform": props.get("platform"),
            }
        }
