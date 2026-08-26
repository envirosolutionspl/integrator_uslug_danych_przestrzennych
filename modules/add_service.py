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
import lxml
from xml.etree import ElementTree as ET # nosec B405

from owslib.util import ServiceException
from owslib.wcs import WebCoverageService
from owslib.wfs import WebFeatureService
from owslib.wms import WebMapService
from owslib.wmts import WebMapTileService

from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer

from ..constants import SERVICES_REQUEST_TIMEOUT_SECONDS, SERVICES_NAMESPACES
from ..utils import ServiceAPI

from qgis.PyQt.QtCore import QEventLoop, QObject, QTimer

class legacyWebCoverageService:
    """Klasa dla QGIS w wersji 3.28 i 3.34, gdzie występują problemy z SSL"""
    def __init__(self):
        self.service_api = ServiceAPI()
        self.contents = []

    def __init__(self, url: str):
        self.service_api = ServiceAPI()
        self.contents = []
        self.updateContents(url=url)

    def updateContents(self, url: str):
        self.contents = []
        parser = lxml.etree.XMLParser(
            resolve_entities=False,  # Prevent XXE
            no_network=True,         # Disable network access
            recover=False            # Avoid silent error recovery
        )
        
        try:
            is_ok, capabilities_xml = self.service_api.getRequest(url)
            if not is_ok:
                return False
            capabilities_root = lxml.etree.fromstring(capabilities_xml.encode('utf-8'), parser=parser)
        except ET.ParseError:
            return False
        except Exception as e:
            return False
        
        ns = SERVICES_NAMESPACES.get("WCS")
        for node in capabilities_root.findall('.//wcs:CoverageSummary', ns):
            cid = node.find('wcs:CoverageId', ns)
            if cid is None or not cid.text:
                continue
            name = cid.text.strip()
            self.contents.append(name)
        return True

    def getContents(self):
        return self.contents
        

class AddOGCService(QObject):

    def __init__(self):
        super().__init__()
        self.downloaded_layers = []
        self.loop = QEventLoop()
        self.cancel_tasks = False


    def _addMapLayer(self, layer) -> bool:
        """Dodaje poprawna warstwe do projektu QGIS."""
        if not layer.isValid():
            return False
        QgsProject.instance().addMapLayer(layer)
        return True
    
    def cancelTasks(self):
        """Wystawia flagę wymuszającą zatrzymanie dodwania usług"""
        self.cancel_tasks = True
        
    def addServices(self):
        """Finalizuje proces dodawania usług wrzucając zawartość kolejki warstw do projektu QGIS"""
        result = {}
        for layer in self.downloaded_layers:
            try:
                result[layer['name']] = self._addMapLayer(layer['layer'])
            except Exception:
                result[layer['name']] = False
        self.clearCache()
        return result

    def downloadServices(self, name: str, url: str, service_type: str) -> bool:
        """Pobiera GetCapabilities dla wybranego endpointu i dodaje znalezione warstwy do QGIS."""
        self.cancel_tasks = False
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
        return False

    def clearCache(self):
        """Czyści kolejkę usług do dodania, np. w przypadku anulowania operacji"""
        self.downloaded_layers = []

    def _createQgsLayer(self, service_uri, service_name, service_type, layer_type="raster"):
        """Przygotowywuje nową wartstwę nie blokując okien dialogowych"""

        def _tick():
            self.loop.processEvents()

        # Zapewnienie obsługi pętli zdarzeń Qt
        timer = QTimer(self)
        timer.timeout.connect(_tick)
        timer.start(200)

        if layer_type == "raster":
            layer = QgsRasterLayer(service_uri, service_name, service_type)
        else:
            layer = QgsVectorLayer(service_uri, service_name, service_type)

        timer.stop()

        if self.cancel_tasks:
            return None, True
        return layer, False

    def _processWcsLayer(self, name: str, url: str) -> bool:
        """Tworzy warstwy rastrowe WCS z elementow CoverageSummary."""
        source_not_parsed = True

        for ver in ('1.0.0', '1.1.1'):
            try:
                service = WebCoverageService(url, version=ver, timeout=SERVICES_REQUEST_TIMEOUT_SECONDS)
                source_not_parsed = False
                break
            except Exception:
                source_not_parsed = True         

        if source_not_parsed:
            service = legacyWebCoverageService(url)

        encoded_url = url.split('?')[0].replace('&', '%26') + '?'
        ok = False
        for coverage_id in service.contents:
            uri = f'identifier={coverage_id}&url={encoded_url}'
            layer, is_canceled = self._createQgsLayer(
                uri, 
                f'WCS - {coverage_id}', 
                'wcs',
            )
            if is_canceled:
                return False
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
            get_map = service.getOperationByName('GetMap')
            format_name = get_map.formatOptions[0]
            style_name = list(layer_info.styles.keys())[0] if layer_info.styles else ''
            uri = f'url={service.url}&layers={layer_name}&styles={style_name}&format={format_name}'
            layer, is_canceled = self._createQgsLayer(
                uri, 
                f'WMS - {layer_info.title or layer_name}', 
                'wms',
            )
            if is_canceled:
                return False
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
        return ok

    def _processWfsLayer(self, name: str, url: str) -> bool:
        """Tworzy warstwy wektorowe WFS z elementow FeatureType."""
        service = WebFeatureService(url, version='2.0.0', timeout=SERVICES_REQUEST_TIMEOUT_SECONDS)
        base_url = url.split('?')[0]
        ok = False
        for feature_name, feature_info in service.contents.items():
            format_name = layer_info.formats[0]
            uri = f"url='{base_url}' typename='{feature_name}' pagingEnabled='true' version='auto'"
            layer, is_canceled = self._createQgsLayer(
                uri, 
                f'WFS - {feature_info.title or feature_name}', 
                'WFS',
                layer_type="vector",
            )
            if is_canceled:
                return False
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
            format_name = layer_info.formats[0]
            style_name = list(layer_info.styles.keys())[0]
            uri = f'format={format_name}&layers={layer_name}&styles={style_name}&tileMatrixSet={tile_matrix_set}&url={encoded_url}'
            layer, is_canceled = self._createQgsLayer(
                uri, 
                f'WMTS - {layer_name}', 
                'wms',
            )
            if is_canceled:
                return False
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
