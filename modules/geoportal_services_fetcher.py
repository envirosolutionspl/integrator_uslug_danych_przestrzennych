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
 *       email                : gis@envirosolutions.pl                     *
 *       git sha              : $Format:%H$                                *
 ***************************************************************************/
"""
import re
from lxml import html
from typing import Dict, Union, List, Any, Tuple

from ..constants import (    
    # Services Links
    GEOPORTAL_WCS_URL,
    GEOPORTAL_WFS_URL,
    GEOPORTAL_WMS_WMTS_URL,

    # Others
    SERVICES_REQUEST_TIMEOUT_SECONDS,
)

from ..utils import NetworkUtils

class GeoportalServicesFetcher:
    def __init__(self):
        pass

    def getServicesDict(self, url: str) -> Tuple[Dict, List]:
        serv_rows = []
        is_success, content = NetworkUtils().fetchContent(url, timeout_ms= SERVICES_REQUEST_TIMEOUT_SECONDS * 1000)
        if not is_success:
            return serv_rows

        tree = html.fromstring(content)
        for table in tree.xpath("//table"):
            for row in table.xpath(".//tr[position()>1]"):
                columns = row.xpath(".//td")
                if len(columns) >= 4:
                    dataset_name = columns[1].text_content().strip()
                    link_tag = columns[3].xpath(".//a")
                    if link_tag and "href" in link_tag[0].attrib:
                        service_url = link_tag[0].attrib["href"]
                        serv_rows.append(
                        {
                            'dataset_name': re.sub(r"\s+", " ", dataset_name),
                            'service_type': 'None',
                            'url': service_url.strip(),
                        })

        return serv_rows

    def getWmsWmtsServices(self) -> List:
        return self.getServicesDict(GEOPORTAL_WMS_WMTS_URL)

    def getWfsWcsServices(self) -> List:
        result =  self.getServicesDict(GEOPORTAL_WFS_URL)
        result.extend(self.getServicesDict(GEOPORTAL_WCS_URL))  
        return result