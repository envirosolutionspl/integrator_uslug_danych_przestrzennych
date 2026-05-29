from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from xml.etree.ElementTree import ParseError

import requests
from owslib.util import ServiceException
from owslib.wcs import WebCoverageService
from owslib.wfs import WebFeatureService
from owslib.wms import WebMapService
from owslib.wmts import WebMapTileService

from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer

from ..utils import NetworkManager


class AddOGCService:
    def __init__(self, network_manager: NetworkManager):
        self.network_manager = network_manager

    @staticmethod
    def _addMapLayer(layer) -> bool:
        """Dodaje poprawna warstwe do projektu QGIS."""
        if not layer.isValid():
            return False
        QgsProject.instance().addMapLayer(layer)
        return True

    @staticmethod
    def addService(service_type: str, url: str) -> bool:
        """Dodaje usluge OGC do projektu QGIS."""
        try:
            if service_type == 'WMS':
                return AddOGCService._processWmsLayer(url)
            if service_type == 'WMTS':
                return AddOGCService._processWmtsLayer(url)
            if service_type == 'WFS':
                return AddOGCService._processWfsLayer(url)
            if service_type == 'WCS':
                return AddOGCService._processWcsLayer(url)
        except ServiceException:
            return False
        except ParseError:
            return False
        except requests.exceptions.RequestException:
            return False

    @staticmethod
    def _processWcsLayer(url: str) -> bool:
        """Tworzy warstwy rastrowe WCS z elementow CoverageSummary."""
        service = WebCoverageService(url, version='1.1.1')
        encoded_url = url.split('?')[0].replace('&', '%26') + '?'
        ok = False
        for coverage_id in service.contents:
            uri = f'identifier={coverage_id}&url={encoded_url}'
            layer = QgsRasterLayer(uri, f'WCS - {coverage_id}', 'wcs')
            ok |= AddOGCService._addMapLayer(layer)
        return ok

    @staticmethod
    def _processWmsLayer(url: str) -> bool:
        """Tworzy warstwy rastrowe WMS z nazw i tytulow warstw w GetCapabilities."""
        try:
            service = WebMapService(url, version='1.3.0')
        except Exception:
            service = WebMapService(url, version='1.1.1')
        ok = False
        for layer_name, layer_info in service.contents.items():
            uri = f'url={service.url}&layers={layer_name}&styles=&format=image/png'
            layer = QgsRasterLayer(uri, f'WMS - {layer_info.title or layer_name}', 'wms')
            ok |= AddOGCService._addMapLayer(layer)
        return ok

    @staticmethod
    def _processWfsLayer(url: str) -> bool:
        """Tworzy warstwy wektorowe WFS z elementow FeatureType."""
        service = WebFeatureService(url, version='2.0.0')
        base_url = url.split('?')[0]
        ok = False
        for feature_name, feature_info in service.contents.items():
            uri = f"url='{base_url}' typename='{feature_name}' pagingEnabled='true' version='auto'"
            layer = QgsVectorLayer(uri, f'WFS - {feature_info.title or feature_name}', 'WFS')
            ok |= AddOGCService._addMapLayer(layer)
        return ok

    @staticmethod
    def _processWmtsLayer(url: str) -> bool:
        """Tworzy warstwy kafelkowe WMTS z identyfikatora warstwy i TileMatrixSet."""
        service = WebMapTileService(url)
        encoded_url = url.replace('&', '%26')
        ok = False
        for layer_name, layer_info in service.contents.items():
            tile_matrix_set = (
                layer_info.tilematrixsetlinks[0].tilematrixset
                if layer_info.tilematrixsetlinks else None
            )
            if not tile_matrix_set:
                continue
            uri = f'format=image/png&layers={layer_name}&styles=&tileMatrixSet={tile_matrix_set}&url={encoded_url}'
            layer = QgsRasterLayer(uri, f'WMTS - {layer_name}', 'wms')
            ok |= AddOGCService._addMapLayer(layer)
        return ok