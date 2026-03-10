from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer

from ..constants import RESULT_SERVICE_TAG, SERVICES_NAMESPACES
from ..utils import NetworkManager


class AddOGCService:
    def __init__(self, network_manager: NetworkManager):
        self.network_manager = network_manager

    def checkServiceResponse(self, url: str) -> bool:
        result = self.network_manager.getRequest(url)
        return bool(result and RESULT_SERVICE_TAG in result)

    def detectServiceType(self, url: str, services: List[str]) -> Optional[str]:
        for service in services:
            if service.casefold() in url.casefold():
                capabilities_url = f"{url}{'' if '?' in url else f'?service={service}&request=GetCapabilities'}"
                if self.checkServiceResponse(capabilities_url):
                    return service
        for service in services:
            capabilities_url = f"{url}{'' if '?' in url else f'?service={service}&request=GetCapabilities'}"
            if self.checkServiceResponse(capabilities_url):
                return service
        return None

    @staticmethod
    def processService(service_type: str, capabilities_xml: str, url: str) -> bool:
        root = ET.fromstring(capabilities_xml)
        namespaces = AddOGCService._getNamespaces(service_type)
        if service_type == 'WCS':
            return AddOGCService._processWcsLayers(root, namespaces, url)
        if service_type == 'WFS':
            return AddOGCService._processWfsLayers(root, namespaces, url)
        if service_type == 'WMS':
            return AddOGCService._processWmsLayers(root, namespaces, url)
        if service_type == 'WMTS':
            return AddOGCService._processWmtsLayers(root, namespaces, url)
        return False

    def addService(self, url: str, service_type: str) -> bool:
        get_capabilities = f"{url}{'' if '?' in url else f'?service={service_type}&request=GetCapabilities'}"
        capabilities_xml = self.network_manager.getRequest(get_capabilities)
        if not capabilities_xml:
            return False
        try:
            return self.processService(service_type, capabilities_xml, url)
        except ET.ParseError:
            return False

    @staticmethod
    def _getNamespaces(service_type: str) -> Dict[str, str]:
        return SERVICES_NAMESPACES.get(service_type)

    @staticmethod
    def _processWcsLayers(root: ET.Element, namespaces: Dict[str, str], url: str) -> bool:
        if_add_layer = False
        coverage_elements = root.findall('.//wcs:CoverageSummary', namespaces)
        for coverage in coverage_elements:
            coverage_id = coverage.find('wcs:CoverageId', namespaces).text
            uri = f"bbox=...&identifier={coverage_id}&url={url}"
            wcs_layer = QgsRasterLayer(uri, f'WCS Layer - {coverage_id}', 'wcs')
            if wcs_layer.isValid():
                QgsProject.instance().addMapLayer(wcs_layer)
                if_add_layer = True
        return if_add_layer

    @staticmethod
    def _processWfsLayers(root: ET.Element, namespaces: Dict[str, str], url: str) -> bool:
        if_add_layer = False
        feature_types = root.findall('.//wfs:FeatureType', namespaces)
        for feature_type in feature_types:
            name_element = feature_type.find('wfs:Name', namespaces)
            title_element = feature_type.find('wfs:Title', namespaces)
            if name_element is None or title_element is None:
                continue

            feature_type_name = name_element.text
            feature_title_name = title_element.text
            uri = (
                f"url='{url.replace('?service=WFS&request=GetCapabilities', '')}' "
                f"typename='{feature_type_name}' "
                "pagingEnabled='true' "
                "version='auto'"
            )
            wfs_layer = QgsVectorLayer(uri, f'WFS Layer - {feature_title_name}', 'WFS')
            if wfs_layer.isValid():
                QgsProject.instance().addMapLayer(wfs_layer)
                if_add_layer = True
        return if_add_layer

    @staticmethod
    def _processWmsLayers(root: ET.Element, namespaces: Dict[str, str], url: str) -> bool:
        if_add_layer = False
        layers_name = root.findall('.//wms:Layer/wms:Name', namespaces)
        layers_title = root.findall('.//wms:Layer/wms:Title', namespaces)

        if not layers_name:
            layers_name = root.findall('.//Layer/Name')
            layers_title = root.findall('.//Layer/Title')

        for name, title in zip(layers_name, layers_title):
            wms_name = name.text
            wms_title = title.text
            if 'arcgis' in url:
                wms_uri = (
                    'contextualWMSLegend=0&'
                    'dpiMode=7&'
                    'featureCount=10&'
                    'format=image/png&'
                    'layers=0&styles&'
                    'tilePixelRatio=0&'
                    f'url={url}'
                )
            else:
                wms_uri = f'url={url}&layers={wms_name}&styles=&format=image/png'

            wms_layer = QgsRasterLayer(wms_uri, f'WMS Layer - {wms_title}', 'wms')
            if wms_layer.isValid():
                QgsProject.instance().addMapLayer(wms_layer)
                if_add_layer = True

        return if_add_layer

    @staticmethod
    def _processWmtsLayers(root: ET.Element, namespaces: Dict[str, str], url: str) -> bool:
        if_add_layer = False
        url = f"{url}{'' if '?' in url else '?service=WMTS&request=GetCapabilities'}"
        layers = root.findall('.//wmts:Layer', namespaces)
        for layer in layers:
            layer_identifier = layer.find('ows:Identifier', namespaces).text
            tile_matrix_set = layer.find('.//wmts:TileMatrixSet', namespaces).text
            wmts_uri = (
                'contextualWMSLegend=0&'
                'dpiMode=7&'
                'featureCount=10&'
                'format=image/png&'
                f'layers={layer_identifier}&'
                'styles=default&'
                f'tileMatrixSet={tile_matrix_set}&'
                'tilePixelRatio=0&'
                f"url={url.replace('&', '%26')}"
            )
            wmts_layer = QgsRasterLayer(wmts_uri, f'WMTS Layer - {layer_identifier}', 'wms')
            if wmts_layer.isValid():
                QgsProject.instance().addMapLayer(wmts_layer)
                if_add_layer = True
        return if_add_layer
