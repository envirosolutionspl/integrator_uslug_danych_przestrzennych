import json
from typing import Dict, List

from ..constants import REST_API_BASE_URL, REST_ENDPOINT_COUNTRY
from ..https_adapter import NetworkManager


class CountryUrlsFetcher:
    def __init__(self, manager=None):
        self.manager = manager or NetworkManager()

    def fetchCountryUrls(self) -> List[Dict[str, str]]:
        result = self.manager.getRequest(REST_API_BASE_URL + REST_ENDPOINT_COUNTRY)
        if not result:
            return []
        try:
            payload = json.loads(result)
        except ValueError:
            return []

        if payload.get('status') != 'success':
            return []

        rawData = payload.get('data')
        if not isinstance(rawData, list):
            return []
        return self.normalizeCountryUrls(rawData)

    def normalizeCountryUrls(self, rawData: List[Dict[str, str]]) -> List[Dict[str, str]]:
        rows = []
        for row in rawData:
            if not isinstance(row, dict):
                continue
            datasetName = str(row.get('dataset_name', '')).strip()
            serviceType = str(row.get('service_type', '')).strip().upper()
            url = str(row.get('url', '')).strip()
            if not datasetName or not serviceType or not url:
                continue
            rows.append(
                {
                    'datasetName': datasetName,
                    'serviceType': serviceType,
                    'url': url,
                }
            )
        return rows

    def getCountryUrlsByServiceType(self, countryRows: List[Dict[str, str]], serviceType: str) -> List[Dict[str, str]]:
        normalizedType = serviceType.strip().upper()
        return [row for row in countryRows if row.get('serviceType') == normalizedType]
