# -*- coding: utf-8 -*-
"""
/***************************************************************************
 * Integrator Uslug Danych Przestrzennych                                  *
 *                                 A QGIS plugin                           *
 * Wtyczka umożliwia prezentację danych z serwisów WMS, WMTS, WFS i WCS    *
 * w postaci warstw w QGIS. Wtyczka wykorzystuje dane z Ewidencji Zbiorów  *
 * i Usług oraz strony geoportal.gov.pl                                    *
 * ----------------------------------------------------------------------- *
 *       begin                : 2026-05-28                                 *
 *       copyright            : (C) 2026 by EnviroSolutions Sp. z o.o.     *
 *       email                : office@envirosolutions.pl                  *
 *       git sha              : $Format:%H$                                *
 ***************************************************************************/
"""
import json
from typing import Dict, List

from ..constants import REST_API_BASE_URL, REST_ENDPOINT_COUNTRY
from ..utils import NetworkUtils

from ..constants import SERVICES_REQUEST_TIMEOUT_SECONDS

class CountryUrlsFetcher:
    def __init__(self, manager=None):
        pass

    def fetchCountryUrls(self, teryt: str, service_type: str) -> List[Dict[str, str]]:
        url = "/".join([REST_API_BASE_URL.rstrip("/"), REST_ENDPOINT_COUNTRY.lstrip("/"), teryt, service_type])
        is_success, result = NetworkUtils().fetchContent(url, timeout_ms= SERVICES_REQUEST_TIMEOUT_SECONDS * 1000)
        if not result or not is_success:
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
