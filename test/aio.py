import os
import sys
from functools import partial

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import Qt, QSortFilterProxyModel
from qgis.PyQt.QtWidgets import QComboBox, QWidget
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem, QShowEvent
from typing import Any, Dict, Tuple, List, Union
import os.path
import warnings
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import ssl
from lxml import html

EZIUDP_URL = 'https://integracja.gugik.gov.pl/eziudp/index.php'


                


    
class AddOGCService:
    @staticmethod
    def check_service_response(url: str) -> bool:
        try:
            with get_legacy_session().get(url=url, verify=False) as resp:
                if resp.status_code == 200 and "Service" in resp.text:
                    return True
        except requests.RequestException:
            return False
    
    @staticmethod
    def detect_service_type(url: str, services: List[str]) -> None or str:
        for service in services:
            if service.casefold() in lista2:
                capabilities_url = f"{url}{'' if '?' in url else f'?service={service}&request=GetCapabilities'}"
                if AddOGCService.check_service_response(capabilities_url):
                    return service
        for service in services:
            capabilities_url = f"{url}{'' if '?' in url else f'?service={service}&request=GetCapabilities'}"
            if AddOGCService.check_service_response(capabilities_url):
                return service
        return None
    
class CustomHttpAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, ssl_context=self.ssl_context)
        

def get_legacy_session():
    warnings.filterwarnings("ignore", category=ResourceWarning)
    warnings.filterwarnings("ignore", category=InsecureRequestWarning)
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    session = requests.session()
    session.mount('https://', CustomHttpAdapter(ctx))
    session.verify = False
    return session




class EziudpServicesFetcher:
    @staticmethod
    def get_services_dict(url: str, idx: int) -> Dict[str, Union[str, List[str]]]:
        services = {}
        try:
            with get_legacy_session().get(url=url, verify=False) as resp:
                resp.raise_for_status()
        except requests.RequestException:
            return services
        tree = html.fromstring(resp.content)
        table = tree.xpath('//table[contains(@class, "table sortable")]')
        if not table:
            return services
        rows = table[0].xpath('.//tr[position()>1]')
        for row in rows:
            columns = row.xpath('.//td')
            if len(columns) < 6:
                continue
            dataset_name = columns[2].text_content().strip()
            link_tag = columns[idx].xpath('.//a')
            if link_tag:
                links = [link.get('href').strip() for link in link_tag if link.get('href')]
                services[dataset_name] = links if len(links) > 1 else links[0]
        return services

    def get_wms_wmts_services(self, url: str) -> Dict:
        return self.get_services_dict(url, 5)

    def get_wfs_wcs_services(self, url: str) -> Dict:
        return self.get_services_dict(url, 6)

    def get_services_wms_wmts_by_teryt(self, unit_type: str, teryt: str) -> Dict:
        return self.get_wms_wmts_services(f'{EZIUDP_URL}?teryt={teryt}&rodzaj={unit_type}')

    def get_services_wfs_wcs_by_teryt(self, unit_type: str, teryt: str) -> Dict:
        return self.get_wfs_wcs_services(f'{EZIUDP_URL}?teryt={teryt}&rodzaj={unit_type}')

    def get_services_wms_wmts_dict_for_pl(self) -> Dict:
        return self.get_wms_wmts_services(f'{EZIUDP_URL}?teryt=PL')

    def get_services_wfs_wcs_dict_for_pl(self) -> Dict:
        return self.get_wfs_wcs_services(f'{EZIUDP_URL}?teryt=PL')

    # Corrected version of the function
    # def get_services_dict_for_pl(self) -> Dict[str, str]:
    #     services = {
    #         "wms_wmts": self.get_wms_wmts_services(f'{EZIUDP_URL}?teryt=PL'),
    #         "wfs_wcs": self.get_wfs_wcs_services(f'{EZIUDP_URL}?teryt=PL'),
    #         "wms_wmts_dict": self.get_services_wms_wmts_dict_for_pl(),
    #         "wfs_wcs_dict": self.get_services_wfs_wcs_dict_for_pl()
    #     }
    #     return services
    
    def get_services_dict_for_pl(self) -> List[str]:
        links = [
         self.get_wms_wmts_services(f'{EZIUDP_URL}?teryt=PL'),
        self.get_wfs_wcs_services(f'{EZIUDP_URL}?teryt=PL'),
        self.get_services_wms_wmts_dict_for_pl(),
        self.get_services_wfs_wcs_dict_for_pl()
    ]
    
    # Assuming each function returns a dictionary or list of links, 
    # you can extend the list with each individual link.
        flat_links = []
        for link_set in links:
            if isinstance(link_set, list):
                flat_links.extend(link_set)  # Add all links from a list
            elif isinstance(link_set, dict):
                flat_links.extend(link_set.values())  # Add all links from a dictionary
                
        return flat_links

# Create an instance of the class
eziudp_fetcher = EziudpServicesFetcher()

# Call the method on the instance (this will pass `self` automatically)
listalinkow = eziudp_fetcher.get_services_dict_for_pl()

listalinkow2 = []

# Loop through each item in listalinkow
for item in listalinkow:
    # Check if the item is a string
    if isinstance(item, str):
        # Split the string at each comma (',') and add to the new list
        split_items = item.split(',')
        listalinkow2.extend(split_items)
    elif isinstance(item, list):
        # If the item is a list, just add its elements to the new list
        listalinkow2.extend(item)

# Print the new list with separated instances


lista2 = [str(word).casefold() for word in listalinkow2]

def add_service(x):
    selected_url = listalinkow[x]
    services = ['WFS', 'WCS','WMTS', 'WMS']
    service_type = AddOGCService.detect_service_type(selected_url, services)
    if service_type:
        success = 1
    else:
        success = 0
    return success

def add_service_v2(x):
    selected_url = listalinkow2[x]
    services = ['WFS', 'WCS','WMTS', 'WMS']
    service_type = AddOGCService.detect_service_type(selected_url, services)
    if service_type:
        success = 1
    else:
        success = 0
    print(" --- ",selected_url)
    return success
