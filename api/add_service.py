from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer, QgsNetworkAccessManager
from qgis.PyQt.QtCore import QEventLoop, QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest
from typing import Dict
from xml.etree import ElementTree as ET
import requests

from ..constants import SERVICES_NAMESPACES
from ..https_adapter import get_legacy_session


class AddOGCService:
    @staticmethod
    def detect_service_type(url: str, services: list [str]) -> None or str:    
        print('Detection')

        # First, try to detect the service by checking if the service name is in the URL
        for service in services:
            if service.casefold() in url.casefold():
                suffix = '' if '?' in url else f'?service={service}&request=GetCapabilities'
                capabilities_url = f'{url}{suffix}'
                print('Capabilities URL according to URL:', capabilities_url)
                if AddOGCService.check_service_response(capabilities_url):
                    print('Identified service according to URL -', service)
                    return service

        # If not found, try each service by appending parameters
        for service in services:
            suffix = '' if '?' in url else f'?service={service}&request=GetCapabilities'
            capabilities_url = f'{url}{suffix}'
            print('Capabilities URL:', capabilities_url)
            if AddOGCService.check_service_response(capabilities_url):
                print('Identified service -', service)
                return service

        print('Detection failed')
        return None

    @staticmethod
    def check_service_response(url: str) -> bool:
        try:
            with get_legacy_session().get(url=url, verify=False) as resp:
                if resp.status_code == 200 and "<Service>" in resp.text:
                    return True
        except requests.RequestException:
            return False

    @staticmethod
    def add_service(url: str, service_type: str) -> bool:
        add_layer = False
        formatURL = '' if '?' in url else f'?service={service_type}&request=GetCapabilities'
        get_capabilities_url = f'{url}{formatURL}'
        print('Service - ', service_type)
        if service_type in ['WCS', 'WFS', 'WMTS']:
            network_manager = QgsNetworkAccessManager.instance()
            request = QNetworkRequest(QUrl(get_capabilities_url))
            reply = network_manager.get(request)
            event_loop = QEventLoop()
            reply.finished.connect(event_loop.quit)
            event_loop.exec_()
            if reply.error() != reply.NoError:
                reply.deleteLater()
                return False
            capabilities_xml = reply.readAll().data().decode()
            reply.deleteLater()
        elif service_type == 'WMS':
            try:
                with get_legacy_session().get(url=get_capabilities_url, verify=False) as resp:
                    if resp.status_code != 200:
                        return False
                    capabilities_xml = resp.content.decode()
            except:
                return False
        try:
            root = ET.fromstring(capabilities_xml)
            namespaces = AddOGCService._get_namespaces(service_type)
            if service_type == 'WCS':
                add_layer = AddOGCService._process_wcs_layers(root, namespaces, url)
            elif service_type == 'WFS':
                add_layer = AddOGCService._process_wfs_layers(root, namespaces, url)
            elif service_type == 'WMS':
                add_layer = AddOGCService._process_wms_layers(root, namespaces, url)
            elif service_type == 'WMTS':
                add_layer = AddOGCService._process_wmts_layers(root, namespaces, url)
            return add_layer
        except ET.ParseError:
            return False

    @staticmethod
    def _get_namespaces(service_type: str) -> Dict[str, str]:
        return SERVICES_NAMESPACES.get(service_type)

    @staticmethod
    def _process_wcs_layers(root: ET.Element, namespaces: Dict[str, str], url: str) -> bool:
        add_layer = False
        coverage_elements = root.findall('.//wcs:CoverageSummary', namespaces)
        for coverage in coverage_elements:
            coverage_id = coverage.find('wcs:CoverageId', namespaces).text
            uri = (
                f"bbox=...&"
                f"identifier={coverage_id}&"
                f"url={url}"
            )
            print('WCS uri', uri)
            wcs_layer = QgsRasterLayer(uri, f'WCS Layer - {coverage_id}', 'wcs')
            if wcs_layer.isValid():
                QgsProject.instance().addMapLayer(wcs_layer)
                add_layer = True
        return add_layer

    @staticmethod
    def _process_wfs_layers(root: ET.Element, namespaces: Dict[str, str], url: str) -> bool:
        add_layer = False
        feature_types = root.findall('.//wfs:FeatureType', namespaces)
        for feature_type in feature_types:
            name_element = feature_type.find('wfs:Name', namespaces)
            if name_element is not None:
                feature_type_name = name_element.text
            else:
                continue
            title_element = feature_type.find('ows:Title', namespaces)
            if title_element is not None:
                layer_name = title_element.text
            else:
                layer_name = feature_type_name

            uri = (
                f"{url}?service=WFS&"
                f"typename={feature_type_name}&"
                f"outputFormat=GML3"
            )
            print('WFS uri', uri)
            wfs_layer = QgsVectorLayer(uri, f'WFS Layer - {layer_name}', 'WFS')
            if wfs_layer.isValid():
                QgsProject.instance().addMapLayer(wfs_layer)
                add_layer = True
        return add_layer

    @staticmethod
    def _process_wms_layers(root: ET.Element, namespaces: Dict[str, str], url: str) -> bool:
        add_layer = False
        layers = root.findall(".//wms:Layer/wms:Name", namespaces)
        for layer_elem in layers:
            layer_name = layer_elem.text
            wms_uri = f"url={url}&layers={layer_name}&styles=&format=image/png"
            print('WMS uri - ', wms_uri)
            wms_layer = QgsRasterLayer(wms_uri, f'WMS Layer - {layer_name}', 'wms')
            if wms_layer.isValid():
                QgsProject.instance().addMapLayer(wms_layer)
                add_layer = True
        return add_layer

    def _process_wmts_layers(root: ET.Element, namespaces: Dict[str, str], url: str) -> bool:
        add_layer = False
        get_capabilities_url = f"{url}?service=WMTS&request=GetCapabilities"
        layers = root.findall('.//wmts:Layer', namespaces)
        for layer in layers:
            layer_identifier = layer.find('ows:Identifier', namespaces).text
            tile_matrix_set = layer.find('.//wmts:TileMatrixSet', namespaces).text
            wmts_uri = (
                "contextualWMSLegend=0&"
                "dpiMode=7&"
                "featureCount=10&"
                "format=image/png&"
                f"layers={layer_identifier}&"
                "styles=default&"
                f"tileMatrixSet={tile_matrix_set}&"
                "tilePixelRatio=0&"
                f"url={get_capabilities_url.replace('&', '%26')}"
                )
            print('WMTS uri - ', wmts_uri)
            wmts_layer = QgsRasterLayer(wmts_uri, f'WMTS Layer - {layer_identifier}', 'wms')
            if wmts_layer.isValid():
                QgsProject.instance().addMapLayer(wmts_layer)
                add_layer = True
        return add_layer

