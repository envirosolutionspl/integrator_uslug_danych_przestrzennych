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
from typing import Dict
from xml.etree import ElementTree as ET # nosec B405
import lxml

from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer

from ..constants import SERVICES_NAMESPACES
from ..utils import NetworkManager

class AddOGCService:
    def __init__(self, network_manager: NetworkManager):
        self.network_manager = network_manager
        self.url_list = []

    def processService(self, service_type: str, capabilities_xml: str, url: str) -> bool:
        """Rozdziela XML GetCapabilities na warstwy QGIS zgodnie z typem uslugi."""
        parser = lxml.etree.XMLParser(
                resolve_entities=False,  # Prevent XXE
                no_network=True,         # Disable network access
                recover=False            # Avoid silent error recovery
            )
        
        capabilities_root = lxml.etree.fromstring(capabilities_xml.encode('utf-8'), parser=parser)
        xml_namespaces = AddOGCService._getNamespaces(service_type)
        if service_type == 'WCS':
            return AddOGCService._processWcsLayers(capabilities_root, xml_namespaces, url)
        if service_type == 'WFS':
            return AddOGCService._processWfsLayers(capabilities_root, xml_namespaces, url)
        if service_type == 'WMS':
            return AddOGCService._processWmsLayers(capabilities_root, xml_namespaces, url)
        if service_type == 'WMTS':
            return AddOGCService._processWmtsLayers(capabilities_root, xml_namespaces, url)
        return False

    def addService(self, url: str, service_type: str) -> bool:
        """Pobiera GetCapabilities dla wybranego endpointu i dodaje znalezione warstwy do QGIS."""
        capabilities_url = f"{url}{'' if '?' in url else f'?service={service_type}&request=GetCapabilities'}"
        capabilities_xml = self.network_manager.getRequest(capabilities_url)
        if not capabilities_xml:
            return False
        try:
            return self.processService(service_type, capabilities_xml, url)
        except ET.ParseError:
            return False
        
    def downloadServices(self, name: str, url: str, service_type: str) -> bool:
        """Pobiera GetCapabilities dla wybranego endpointu i dodaje znalezione warstwy do QGIS."""
        capabilities_url = f"{url}{'' if '?' in url else f'?service={service_type}&request=GetCapabilities'}"
        capabilities_xml = self.network_manager.getRequest(capabilities_url)
        self.url_list.append(
            {
                'name': name,
                'xml': capabilities_xml,
                'url': url,
                'service_type': service_type,
            }
        )

    def addServices(self):
        result = {}
        for service in self.url_list:
            capabilities_xml = service['xml']
            if not capabilities_xml:
                result[service['name']] = False
                continue
            try:
                result[service['name']] = self.processService(service['service_type'], capabilities_xml, service['url'])
            except ET.ParseError:
                result[service['name']] = False
        self.url_list.clear()
        return result
    
    def clearCache(self):
        self.url_list.clear()

    @staticmethod
    def _getNamespaces(service_type: str) -> Dict[str, str]:
        """Zwraca przestrzenie nazw XML potrzebne do odczytu danego typu uslugi OGC."""
        return SERVICES_NAMESPACES.get(service_type)

    @staticmethod
    def _add_map_layer(layer) -> bool:
        """Dodaje poprawna warstwe do projektu QGIS."""
        if not layer.isValid():
            return False
        QgsProject.instance().addMapLayer(layer)
        return True

    @staticmethod
    def _processWcsLayers(root: ET.Element, ns: Dict[str, str], url: str) -> bool:
        """Tworzy warstwy rastrowe WCS z elementow CoverageSummary."""
        enc = url.replace('&', '%26')
        ok = False
        for node in root.findall('.//wcs:CoverageSummary', ns):
            cid = node.find('wcs:CoverageId', ns)
            if cid is None or not cid.text:
                continue
            name = cid.text.strip()
            uri = f'identifier={name}&url={enc}'
            layer = QgsRasterLayer(uri, f'WCS Layer - {name}', 'wcs')
            ok |= AddOGCService._add_map_layer(layer)
        return ok

    @staticmethod
    def _processWfsLayers(root: ET.Element, ns: Dict[str, str], url: str) -> bool:
        """Tworzy warstwy wektorowe WFS z elementow FeatureType."""
        base = url.replace('?service=WFS&request=GetCapabilities', '')
        ok = False
        for ft in root.findall('.//wfs:FeatureType', ns):
            n, t = ft.find('wfs:Name', ns), ft.find('wfs:Title', ns)
            if n is None or t is None or not n.text or not t.text:
                continue
            uri = (
                f"url='{base}' typename='{n.text}' pagingEnabled='true' version='auto'"
            )
            layer = QgsVectorLayer(uri, f'WFS Layer - {t.text}', 'WFS')
            ok |= AddOGCService._add_map_layer(layer)
        return ok

    @staticmethod
    def _processWmsLayers(root: ET.Element, ns: Dict[str, str], url: str) -> bool:
        """Tworzy warstwy rastrowe WMS z nazw i tytulow warstw w GetCapabilities."""
        names = root.findall('.//wms:Layer/wms:Name', ns)
        titles = root.findall('.//wms:Layer/wms:Title', ns)
        if not names:
            names = root.findall('.//Layer/Name')
            titles = root.findall('.//Layer/Title')
        ok = False
        for name_el, title_el in zip(names, titles):
            if not name_el.text or not title_el.text:
                continue
            uri = f'url={url}&layers={name_el.text}&styles=&format=image/png'
            layer = QgsRasterLayer(uri, f'WMS Layer - {title_el.text}', 'wms')
            ok |= AddOGCService._add_map_layer(layer)
        return ok

    @staticmethod
    def _processWmtsLayers(root: ET.Element, ns: Dict[str, str], url: str) -> bool:
        """Tworzy warstwy kafelkowe WMTS z identyfikatora warstwy i TileMatrixSet."""
        enc = url.replace('&', '%26')
        ok = False
        for node in root.findall('.//wmts:Layer', ns):
            id_el = node.find('ows:Identifier', ns)
            mtx_el = node.find('.//wmts:TileMatrixSet', ns)
            if id_el is None or mtx_el is None or not id_el.text or not mtx_el.text:
                continue
            lid, matrix = id_el.text, mtx_el.text
            uri = f'format=image/png&layers={lid}&styles=&tileMatrixSet={matrix}&url={enc}'
            layer = QgsRasterLayer(uri, f'WMTS Layer - {lid}', 'wms')
            ok |= AddOGCService._add_map_layer(layer)
        return ok
