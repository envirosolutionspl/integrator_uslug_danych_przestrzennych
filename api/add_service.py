from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer, QgsNetworkAccessManager
from qgis.PyQt.QtCore import QEventLoop, QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest
from typing import Dict, List
from xml.etree import ElementTree as ET
import requests

from ..constants import SERVICES_NAMESPACES
from ..https_adapter import get_legacy_session


class AddOGCService:
    @staticmethod
    def detect_service_type(url: str, services: List[str]) -> None or str:
        for service in services:
            if service.casefold() in url.casefold():
                capabilities_url = f"{url}{'' if '?' in url else f'?service={service}&request=GetCapabilities'}"
                if AddOGCService.check_service_response(capabilities_url):
                    return service
        for service in services:
            capabilities_url = f"{url}{'' if '?' in url else f'?service={service}&request=GetCapabilities'}"
            if AddOGCService.check_service_response(capabilities_url):
                return service
        return None

    @staticmethod
    def check_service_response(url: str) -> bool:
        try:
            with get_legacy_session().get(url=url, verify=False) as resp:
                if resp.status_code == 200 and "Service" in resp.text:
                    return True
        except requests.RequestException:
            return False

    @staticmethod
    def process_service(service_type, capabilities_xml, url):
        root = ET.fromstring(capabilities_xml)
        namespaces = AddOGCService._get_namespaces(service_type)
        if service_type == 'WCS':
            return AddOGCService._process_wcs_layers(root, namespaces, url)
        elif service_type == 'WFS':
            return AddOGCService._process_wfs_layers(root, namespaces, url)
        elif service_type == 'WMS':
            return AddOGCService._process_wms_layers(root, namespaces, url)
        elif service_type == 'WMTS':
            return AddOGCService._process_wmts_layers(root, namespaces, url)
        return False

    @staticmethod
    def fetch_capabilities(url: str) -> str or None:
        network_manager = QgsNetworkAccessManager.instance()
        request = QNetworkRequest(QUrl(url))
        reply = network_manager.get(request)
        event_loop = QEventLoop()
        reply.finished.connect(event_loop.quit)
        event_loop.exec_()
        if reply.error() != reply.NoError:
            reply.deleteLater()
            return None
        redirect_url = reply.attribute(QNetworkRequest.RedirectionTargetAttribute)
        if redirect_url:
            return AddOGCService.fetch_capabilities(redirect_url.toString())
        capabilities_xml = reply.readAll().data().decode('utf-8')
        reply.deleteLater()
        return capabilities_xml

    @staticmethod
    def add_service(url: str, service_type: str) -> bool:
        get_capabilities = f"{url}{'' if '?' in url else f'?service={service_type}&request=GetCapabilities'}"
        if service_type in ['WCS', 'WFS', 'WMTS']:
            capabilities_xml = AddOGCService.fetch_capabilities(get_capabilities)
            if not capabilities_xml:
                return False
        elif service_type == 'WMS':
            try:
                with get_legacy_session().get(url=get_capabilities, verify=False) as resp:
                    if resp.status_code != 200:
                        return False
                    capabilities_xml = resp.content.decode('utf-8')
            except:
                # Fragment niezgodny ze standardem
                return False
        try:
            return AddOGCService.process_service(service_type, capabilities_xml, url)
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
            title_element = feature_type.find('wfs:Title', namespaces)
            
            if name_element is not None and title_element is not None :
                feature_type_name = name_element.text
                feature_title_name = title_element.text
            else:
                continue
            title_element = feature_type.find('ows:Title', namespaces)
            if title_element is not None:
                layer_name = title_element.text
            else:
                layer_name = feature_type_name

            uri = (
                f"url='{url.replace('?service=WFS&request=GetCapabilities', '')}' "
                f"typename='{feature_type_name}' "
                f"pagingEnabled='true' "
                f"version='auto'"
            )
            wfs_layer = QgsVectorLayer(uri, f'WFS Layer - {feature_title_name}', 'WFS')
            if wfs_layer.isValid():
                QgsProject.instance().addMapLayer(wfs_layer)
                add_layer = True
        return add_layer

    @staticmethod
    def _process_wms_layers(root: ET.Element, namespaces: Dict[str, str], url: str) -> bool:
        add_layer = False
        layers_name = root.findall(".//wms:Layer/wms:Name", namespaces)
        layers_title = root.findall(".//wms:Layer/wms:Title", namespaces)

        for name, title in zip(layers_name, layers_title):
            wms_name = name.text
            wms_title = title.text
            if 'arcgis' in url:
                wms_uri = (
                    "contextualWMSLegend=0&"
                    "dpiMode=7&"
                    "featureCount=10&"
                    "format=image/png&"
                    "layers=0&styles&"
                    "tilePixelRatio=0&"
                    f"url={url}"
                )
            else:
                wms_uri = f"url={url}&layers={wms_name}&styles=&format=image/png"
            
            wms_layer = QgsRasterLayer(wms_uri, f'WMS Layer - {wms_title}', 'wms')
            if wms_layer.isValid():
                QgsProject.instance().addMapLayer(wms_layer)
                add_layer = True

        return add_layer

    def _process_wmts_layers(root: ET.Element, namespaces: Dict[str, str], url: str) -> bool:
        add_layer = False
        url = f"{url}{'' if '?' in url else f'?service=WMTS&request=GetCapabilities'}"
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
                f"url={url.replace('&', '%26')}"
                )
            wmts_layer = QgsRasterLayer(wmts_uri, f'WMTS Layer - {layer_identifier}', 'wms')
            if wmts_layer.isValid():
                QgsProject.instance().addMapLayer(wmts_layer)
                add_layer = True
        return add_layer

