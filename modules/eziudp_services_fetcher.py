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
from lxml import html
from typing import Dict, Union, List, Any, Tuple
from urllib.parse import urljoin

from ..constants import (    
    # Services Link
    EZIUDP_BASE_URL,

    # EZIUDP HTML parsing
    XPATH_TABLE_SORTABLE,
    XPATH_TABLE_ROWS,
    XPATH_ROW_COLUMNS,
    XPATH_LINK_TAG,
    MIN_COLUMNS_FOR_ROW,
    DATASET_NAME_COLUMN,
    WMS_WMTS_COLUMN,
    WFS_WCS_COLUMN,

    # EZIUDP fetcher settings
    EZIUDP_WMS_WMTS_NEEDLES,
    EZIUDP_WFS_WCS_NEEDLES,
)

from ..utils import NetworkUtils

class EziudpServicesFetcher:

    def __init__(self):
        pass

    @staticmethod
    def _normalizeHeader(value: str) -> str:
        return " ".join(value.lower().split())

    @staticmethod
    def _resolveServiceColumnIndex(table_node, fallback_idx: int) -> int:
        headers = table_node.xpath(".//tr[1]/*[self::th or self::td]")
        if not headers:
            return fallback_idx

        if fallback_idx == WMS_WMTS_COLUMN:
            needles = EZIUDP_WMS_WMTS_NEEDLES
        elif fallback_idx == WFS_WCS_COLUMN:
            needles = EZIUDP_WFS_WCS_NEEDLES
        else:
            return fallback_idx

        for idx, header in enumerate(headers):
            text = EziudpServicesFetcher._normalizeHeader(header.text_content())
            if any(needle in text for needle in needles):
                return idx

        return fallback_idx
         
    def getServicesDict(self, url: str, idx: int) -> Tuple[Dict[str, Union[str, List[str]]], List]:
        serv_rows = []
        
        is_success, content = NetworkUtils().fetchContent(url, timeout_ms=3000)
        if not is_success:
            return serv_rows
        
        tree = html.fromstring(content)
        table = tree.xpath(XPATH_TABLE_SORTABLE)
        if not table:
            return serv_rows
        resolved_idx = EziudpServicesFetcher._resolveServiceColumnIndex(table[0], idx)
        rows = table[0].xpath(XPATH_TABLE_ROWS)
        for row in rows:
            columns = row.xpath(XPATH_ROW_COLUMNS)
            if len(columns) < MIN_COLUMNS_FOR_ROW:
                continue
            if DATASET_NAME_COLUMN >= len(columns) or resolved_idx >= len(columns):
                continue
            dataset_name = columns[DATASET_NAME_COLUMN].text_content().strip()
            if not dataset_name:
                continue

            link_tags = columns[resolved_idx].xpath(XPATH_LINK_TAG)
            if not link_tags:
                continue

            for link in link_tags:
                href = (link.get("href") or "").strip()
                if not href:
                    continue
                serv_rows.append(
                {
                    'dataset_name': dataset_name,
                    'service_type': 'None',
                    'url': urljoin(url, href),
                })
         
        return serv_rows

    def getWmsWmtsServices(self, url: str) -> List:
        return self.getServicesDict(url, WMS_WMTS_COLUMN)

    def getWfsWcsServices(self, url: str) -> List:
        return self.getServicesDict(url, WFS_WCS_COLUMN)

    def getServicesWmsWmtsByTeryt(self, unit_type: str, teryt: str) -> List:
        return self.getWmsWmtsServices(
            f"{EZIUDP_BASE_URL}?teryt={teryt}&rodzaj={unit_type}",
        )

    def getServicesWfsWcsByTeryt(self, unit_type: str, teryt: str) -> List:
        return self.getWfsWcsServices(
            f"{EZIUDP_BASE_URL}?teryt={teryt}&rodzaj={unit_type}",
        )
