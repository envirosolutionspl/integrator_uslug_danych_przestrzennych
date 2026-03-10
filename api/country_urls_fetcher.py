import json
from typing import Dict, List

from ..constants import REST_API_BASE_URL, REST_ENDPOINT_COUNTRY
from ..utils import NetworkManager


class CountryUrlsFetcher:
    def __init__(self, manager=None):
        if manager is None:
            manager = NetworkManager()
        self.manager = manager

    def fetchCountryUrls(self) -> List[Dict[str, str]]:
        url = "/".join([REST_API_BASE_URL.rstrip("/"), REST_ENDPOINT_COUNTRY.lstrip("/")])
        result = self.manager.getRequest(url)
        if not result:
            return []
        try:
            payload = json.loads(result)
        except ValueError:
            return []

        if payload.get('status') != 'success':
            return []

        raw_data = payload.get('data')
        if not isinstance(raw_data, list):
            return []
        return self.normalizeCountryUrls(raw_data)

    def normalizeCountryUrls(self, raw_data: List[Dict[str, str]]) -> List[Dict[str, str]]:
        rows = []
        for row in raw_data:
            if not isinstance(row, dict):
                continue
            dataset_name = str(row.get('dataset_name', '')).strip()
            service_type = str(row.get('service_type', '')).strip().upper()
            url = str(row.get('url', '')).strip()
            if not dataset_name or not service_type or not url:
                continue
            rows.append(
                {
                    'dataset_name': dataset_name,
                    'service_type': service_type,
                    'url': url,
                }
            )
        return rows

    def getCountryUrlsByServiceType(self, country_rows: List[Dict[str, str]], service_type: str) -> List[Dict[str, str]]:
        normalized_type = service_type.strip().upper()
        return [row for row in country_rows if row.get('service_type') == normalized_type]
