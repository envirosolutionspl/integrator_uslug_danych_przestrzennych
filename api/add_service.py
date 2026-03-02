from typing import Dict, List
from xml.etree import ElementTree as ET

from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer

from ..constants import RESULT_SERVICE_TAG, SERVICES_NAMESPACES
from ..https_adapter import NetworkManager


class AddOGCService:
    @staticmethod
    def detectServiceType(url: str, services: List[str]) -> str:
        for service in services:
            if service.casefold() in url.casefold():
                capabilitiesUrl = f"{url}{'' if '?' in url else f'?service={service}&request=GetCapabilities'}"
                if AddOGCService.checkServiceResponse(capabilitiesUrl):
                    return service
        for service in services:
            capabilitiesUrl = f"{url}{'' if '?' in url else f'?service={service}&request=GetCapabilities'}"
            if AddOGCService.checkServiceResponse(capabilitiesUrl):
                return service
        return None

    @staticmethod
    def checkServiceResponse(url: str) -> bool:
        result = NetworkManager().getRequest(url)
        return bool(result and RESULT_SERVICE_TAG in result)

    @staticmethod
    def processService(serviceType: str, capabilitiesXml: str, url: str) -> bool:
        root = ET.fromstring(capabilitiesXml)
        namespaces = AddOGCService._getNamespaces(serviceType)
        if serviceType == 'WCS':
            return AddOGCService._processWcsLayers(root, namespaces, url)
        if serviceType == 'WFS':
            return AddOGCService._processWfsLayers(root, namespaces, url)
        if serviceType == 'WMS':
            return AddOGCService._processWmsLayers(root, namespaces, url)
        if serviceType == 'WMTS':
            return AddOGCService._processWmtsLayers(root, namespaces, url)
        return False

    @staticmethod
    def addService(url: str, serviceType: str) -> bool:
        getCapabilities = f"{url}{'' if '?' in url else f'?service={serviceType}&request=GetCapabilities'}"
        capabilitiesXml = NetworkManager().getRequest(getCapabilities)
        if not capabilitiesXml:
            return False
        try:
            return AddOGCService.processService(serviceType, capabilitiesXml, url)
        except ET.ParseError:
            return False

    @staticmethod
    def _getNamespaces(serviceType: str) -> Dict[str, str]:
        return SERVICES_NAMESPACES.get(serviceType)

    @staticmethod
    def _processWcsLayers(root: ET.Element, namespaces: Dict[str, str], url: str) -> bool:
        addLayer = False
        coverageElements = root.findall('.//wcs:CoverageSummary', namespaces)
        for coverage in coverageElements:
            coverageId = coverage.find('wcs:CoverageId', namespaces).text
            uri = f"bbox=...&identifier={coverageId}&url={url}"
            wcsLayer = QgsRasterLayer(uri, f'WCS Layer - {coverageId}', 'wcs')
            if wcsLayer.isValid():
                QgsProject.instance().addMapLayer(wcsLayer)
                addLayer = True
        return addLayer

    @staticmethod
    def _processWfsLayers(root: ET.Element, namespaces: Dict[str, str], url: str) -> bool:
        addLayer = False
        featureTypes = root.findall('.//wfs:FeatureType', namespaces)
        for featureType in featureTypes:
            nameElement = featureType.find('wfs:Name', namespaces)
            titleElement = featureType.find('wfs:Title', namespaces)
            if nameElement is None or titleElement is None:
                continue

            featureTypeName = nameElement.text
            featureTitleName = titleElement.text
            uri = (
                f"url='{url.replace('?service=WFS&request=GetCapabilities', '')}' "
                f"typename='{featureTypeName}' "
                "pagingEnabled='true' "
                "version='auto'"
            )
            wfsLayer = QgsVectorLayer(uri, f'WFS Layer - {featureTitleName}', 'WFS')
            if wfsLayer.isValid():
                QgsProject.instance().addMapLayer(wfsLayer)
                addLayer = True
        return addLayer

    @staticmethod
    def _processWmsLayers(root: ET.Element, namespaces: Dict[str, str], url: str) -> bool:
        addLayer = False
        layersName = root.findall('.//wms:Layer/wms:Name', namespaces)
        layersTitle = root.findall('.//wms:Layer/wms:Title', namespaces)

        if not layersName:
            layersName = root.findall('.//Layer/Name')
            layersTitle = root.findall('.//Layer/Title')

        for name, title in zip(layersName, layersTitle):
            wmsName = name.text
            wmsTitle = title.text
            if 'arcgis' in url:
                wmsUri = (
                    'contextualWMSLegend=0&'
                    'dpiMode=7&'
                    'featureCount=10&'
                    'format=image/png&'
                    'layers=0&styles&'
                    'tilePixelRatio=0&'
                    f'url={url}'
                )
            else:
                wmsUri = f'url={url}&layers={wmsName}&styles=&format=image/png'

            wmsLayer = QgsRasterLayer(wmsUri, f'WMS Layer - {wmsTitle}', 'wms')
            if wmsLayer.isValid():
                QgsProject.instance().addMapLayer(wmsLayer)
                addLayer = True

        return addLayer

    @staticmethod
    def _processWmtsLayers(root: ET.Element, namespaces: Dict[str, str], url: str) -> bool:
        addLayer = False
        url = f"{url}{'' if '?' in url else '?service=WMTS&request=GetCapabilities'}"
        layers = root.findall('.//wmts:Layer', namespaces)
        for layer in layers:
            layerIdentifier = layer.find('ows:Identifier', namespaces).text
            tileMatrixSet = layer.find('.//wmts:TileMatrixSet', namespaces).text
            wmtsUri = (
                'contextualWMSLegend=0&'
                'dpiMode=7&'
                'featureCount=10&'
                'format=image/png&'
                f'layers={layerIdentifier}&'
                'styles=default&'
                f'tileMatrixSet={tileMatrixSet}&'
                'tilePixelRatio=0&'
                f"url={url.replace('&', '%26')}"
            )
            wmtsLayer = QgsRasterLayer(wmtsUri, f'WMTS Layer - {layerIdentifier}', 'wms')
            if wmtsLayer.isValid():
                QgsProject.instance().addMapLayer(wmtsLayer)
                addLayer = True
        return addLayer
