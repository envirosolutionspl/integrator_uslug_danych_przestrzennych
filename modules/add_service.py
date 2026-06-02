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
import requests

from owslib.util import ServiceException
from owslib.wcs import WebCoverageService
from owslib.wfs import WebFeatureService
from owslib.wms import WebMapService
from owslib.wmts import WebMapTileService

from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer

from ..constants import SERVICES_REQUEST_TIMEOUT_SECONDS

class AddOGCService:
    def __init__(self):
        self.downloaded_layers = []

    def _addMapLayer(self, layer) -> bool:
        """Dodaje poprawna warstwe do projektu QGIS."""
        if not layer.isValid():
            return False
        QgsProject.instance().addMapLayer(layer)
        return True
        
    def addServices(self):
        result = {}
        for layer in self.downloaded_layers:
            try:
                result[layer['name']] = self._addMapLayer(layer['layer'])
            except Exception:
                result[layer['name']] = False
        self.downloaded_layers = []
        return result

    def downloadServices(self, name: str, url: str, service_type: str) -> bool:
        """Pobiera GetCapabilities dla wybranego endpointu i dodaje znalezione warstwy do QGIS."""
        try:
            if service_type == 'WMS':
                return self._processWmsLayer(name, url)
            if service_type == 'WMTS':
                return self._processWmtsLayer(name, url)
            if service_type == 'WFS':
                return self._processWfsLayer(name, url)
            if service_type == 'WCS':
                return self._processWcsLayer(name, url)
        except ServiceException:
            return False
        except requests.exceptions.RequestException:
            return False

    def clearCache(self):
        self.downloaded_layers = []

    def _processWcsLayer(self, name: str, url: str) -> bool:
        """Tworzy warstwy rastrowe WCS z elementow CoverageSummary."""
        try:
            service = WebCoverageService(url, version='1.0.0', timeout=SERVICES_REQUEST_TIMEOUT_SECONDS)
        except Exception:
            service = WebCoverageService(url, version='1.1.1', timeout=SERVICES_REQUEST_TIMEOUT_SECONDS)
        encoded_url = url.split('?')[0].replace('&', '%26') + '?'
        ok = False
        for coverage_id in service.contents:
            uri = f'identifier={coverage_id}&url={encoded_url}'
            layer = QgsRasterLayer(uri, f'WCS - {coverage_id}', 'wcs')
            if layer.isValid():
                ok |= True
                self.downloaded_layers.append(
                    {
                        'name': name,
                        'layer': layer,
                        'url': url,
                        'service_type': 'WCS',
                    }
                )
        return ok

    def _processWmsLayer(self, name: str, url: str) -> bool:
        """Tworzy warstwy rastrowe WMS z nazw i tytulow warstw w GetCapabilities."""
        try:
            service = WebMapService(url, version='1.3.0', timeout=SERVICES_REQUEST_TIMEOUT_SECONDS)
        except Exception:
            service = WebMapService(url, version='1.1.1', timeout=SERVICES_REQUEST_TIMEOUT_SECONDS)
        ok = False
        for layer_name, layer_info in service.contents.items():
            uri = f'url={service.url}&layers={layer_name}&styles=&format=image/png'
            layer = QgsRasterLayer(uri, f'WMS - {layer_info.title or layer_name}', 'wms')
            if layer.isValid():
                ok |= True
                self.downloaded_layers.append(
                    {
                        'name': name,
                        'layer': layer,
                        'url': url,
                        'service_type': 'WMS',
                    }
                )
        return True

    def _processWfsLayer(self, name: str, url: str) -> bool:
        """Tworzy warstwy wektorowe WFS z elementow FeatureType."""
        service = WebFeatureService(url, version='2.0.0', timeout=SERVICES_REQUEST_TIMEOUT_SECONDS)
        base_url = url.split('?')[0]
        ok = False
        for feature_name, feature_info in service.contents.items():
            uri = f"url='{base_url}' typename='{feature_name}' pagingEnabled='true' version='auto'"
            layer = QgsVectorLayer(uri, f'WFS - {feature_info.title or feature_name}', 'WFS')
            if layer.isValid():
                ok |= True
                self.downloaded_layers.append(
                    {
                        'name': name,
                        'layer': layer,
                        'url': url,
                        'service_type': 'WFS',
                    }
                )
        return ok

    def _processWmtsLayer(self, name: str, url: str) -> bool:
        """Tworzy warstwy kafelkowe WMTS z identyfikatora warstwy i TileMatrixSet."""
        service = WebMapTileService(url, timeout=SERVICES_REQUEST_TIMEOUT_SECONDS)
        encoded_url = url.replace('&', '%26')
        ok = False
        for layer_name, layer_info in service.contents.items():
            tile_matrix_set_link = next(iter(layer_info.tilematrixsetlinks), None) if layer_info.tilematrixsetlinks else None
            tile_matrix_set = getattr(tile_matrix_set_link, 'tilematrixset', tile_matrix_set_link)
            if not tile_matrix_set:
                continue
            uri = f'format=image/png&layers={layer_name}&styles=&tileMatrixSet={tile_matrix_set}&url={encoded_url}'
            layer = QgsRasterLayer(uri, f'WMTS - {layer_name}', 'wms')
            if layer.isValid():
                ok |= True
                self.downloaded_layers.append(
                    {
                        'name': name,
                        'layer': layer,
                        'url': url,
                        'service_type': 'WMTS',
                    }
                )
        return ok
