from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer, QgsNetworkAccessManager
from qgis.PyQt.QtCore import QEventLoop, QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest
from typing import Dict
from xml.etree import ElementTree as ET
import requests


class AddOGCService:
    @staticmethod
    def detect_service_type(url: str) -> None or str:
        for service in ['WFS', 'WCS', 'WMTS', 'WMS']:
            capabilities_url = f'{url}?service={service}&request=GetCapabilities'
            print(capabilities_url)
            try:
                response = requests.get(capabilities_url)
                if response.status_code == 200:
                    return service
            except requests.RequestException:
                return None
        return None

    @staticmethod
    def add_service(url: str, service_type: str) -> None:
        get_capabilities_url = f'{url}?service={service_type}&request=GetCapabilities'
        if service_type in ['WCS', 'WFS', 'WMTS']:
            network_manager = QgsNetworkAccessManager.instance()
            request = QNetworkRequest(QUrl(get_capabilities_url))
            reply = network_manager.get(request)
            event_loop = QEventLoop()
            reply.finished.connect(event_loop.quit)
            event_loop.exec_()
            if reply.error() != reply.NoError:
                reply.deleteLater()
                return
            capabilities_xml = reply.readAll().data().decode()
            reply.deleteLater()
        elif service_type == 'WMS':
            response = requests.get(get_capabilities_url)
            if response.status_code != 200:
                return
            capabilities_xml = response.content.decode()

        try:
            root = ET.fromstring(capabilities_xml)
            namespaces = AddOGCService._get_namespaces(service_type)
            if service_type == 'WCS':
                AddOGCService._process_wcs_layers(root, namespaces, url)
            elif service_type == 'WFS':
                AddOGCService._process_wfs_layers(root, namespaces, url)
            elif service_type == 'WMS':
                AddOGCService._process_wms_layers(root, namespaces, url)
            elif service_type == 'WMTS':
                AddOGCService._process_wmts_layers(root, namespaces, url)
        except ET.ParseError:
            pass

    @staticmethod
    def _get_namespaces(service_type: str) -> Dict[str, str]:
        if service_type == 'WCS':
            return {'wcs': 'http://www.opengis.net/wcs/2.0', 'ows': 'http://www.opengis.net/ows/2.0'}
        elif service_type == 'WFS':
            return {'wfs': 'http://www.opengis.net/wfs/2.0', 'ows': 'http://www.opengis.net/ows/1.1'}
        elif service_type == 'WMS':
            return {'wms': 'http://www.opengis.net/wms'}
        elif service_type == "WMTS":
            return {'wmts': 'http://www.opengis.net/wmts/1.0', 'ows': 'http://www.opengis.net/ows/1.1'}
        return {}

    @staticmethod
    def _process_wcs_layers(root: ET.Element, namespaces: Dict[str, str], url: str) -> None:
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

    @staticmethod
    def _process_wfs_layers(root: ET.Element, namespaces: Dict[str, str], url: str) -> None:
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
            wfs_layer = QgsVectorLayer(uri, f'WFS Layer - {layer_name}', 'WFS')
            if wfs_layer.isValid():
                QgsProject.instance().addMapLayer(wfs_layer)

    @staticmethod
    def _process_wms_layers(root: ET.Element, namespaces: Dict[str, str], url: str) -> None:
        layers = root.findall(".//wms:Layer/wms:Name", namespaces)
        for layer_elem in layers:
            layer_name = layer_elem.text
            wms_uri = f"url={url}&layers={layer_name}&styles=&format=image/png"
            wms_layer = QgsRasterLayer(wms_uri, f'WMS Layer - {layer_name}', 'wms')
            if wms_layer.isValid():
                QgsProject.instance().addMapLayer(wms_layer)

    def _process_wmts_layers(root: ET.Element, namespaces: Dict[str, str], url: str) -> None:
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
            wmts_layer = QgsRasterLayer(wmts_uri, f'WMTS Layer - {layer_identifier}', 'wms')
            if wmts_layer.isValid():
                QgsProject.instance().addMapLayer(wmts_layer)

