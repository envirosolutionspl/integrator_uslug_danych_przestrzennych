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
from typing import Dict, Union, List, Any, Tuple
from urllib.parse import urljoin

from ..constants import (    
    # Services Link
    EZIUDP_BASE_URL,

    # EZIUDP settings
    EZIUDP_WMS_WMTS_NEEDLES,
    EZIUDP_WFS_WCS_NEEDLES,

    # Others
    SERVICE_TYPES,
    TERYT_PL,
)

from ..modules.eziudp_services_fetcher import EziudpServicesFetcher
from ..modules.geoportal_services_fetcher import GeoportalServicesFetcher

class StandaloneUrlsFetcher:

    def __init__(self):
        self.eziudp_services_fetcher = EziudpServicesFetcher()
        self.geoportal_services_fetcher = GeoportalServicesFetcher()

    def fetch(self): 

        # Scrapowanie serwisów WMS oraz WMTS
        wms_wmts_rows = self.eziudp_services_fetcher.getWmsWmtsServices(
            f"{EZIUDP_BASE_URL}?teryt={TERYT_PL}",
        )

        wms_wmts_rows.extend(
            self.geoportal_services_fetcher.getWmsWmtsServices(),
        )

        # Scrapowanie serwisów WCS oraz WFS
        wfs_wcs_rows = self.eziudp_services_fetcher.getWfsWcsServices(
            f"{EZIUDP_BASE_URL}?teryt={TERYT_PL}",
        )

        wfs_wcs_rows.extend(
            self.geoportal_services_fetcher.getWfsWcsServices(),
        )

        # Określenie tag'u 'service_type' do każdego wyniku 
        service_rows = self._fixServiceTypes(
            wms_wmts_rows, EZIUDP_WMS_WMTS_NEEDLES[0], EZIUDP_WMS_WMTS_NEEDLES,
        )

        service_rows.extend(
            self._fixServiceTypes(wfs_wcs_rows, EZIUDP_WFS_WCS_NEEDLES[0], EZIUDP_WFS_WCS_NEEDLES),
        )

        # Usuwanie duplikatów w każdym typie z osobna
        for st in SERVICE_TYPES:
            service_rows = self._removeDoublesByTypes(service_rows, type=st)
        return service_rows
    
    def _fixServiceTypes(self, service_list: List, default='None', option_pool=('None',)):
        " Sprawdza wpisy i próbuje ustalić rodzaj usługi napodstawie url "
        serv_rows = []
        for row in service_list:
            if row['service_type'] == 'None':
                row['service_type'] = default
                for option in option_pool:
                    if option.lower() in row['url'].lower():
                        row['service_type'] = option.upper()

            serv_rows.append(row)
        return serv_rows
    
    def _removeDoublesByTypes(self, service_list: List, type='None'):
        seen = set()         
        serv_rows = []

        for row in service_list:
            if row['service_type'].lower() == type.lower():
                if row['url'] not in seen:
                    seen.add(row['url'])
                    serv_rows.append(row)
            else:
                serv_rows.append(row)

        return serv_rows


