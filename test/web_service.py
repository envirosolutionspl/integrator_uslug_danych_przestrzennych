
from typing import Dict, Union, List
import requests
from lxml import html
import warnings
import ssl
import urllib3
EZIUDP_URL = 'https://integracja.gugik.gov.pl/eziudp/index.php'
from urllib3.exceptions import InsecureRequestWarning
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QToolBar
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem, QShowEvent

@staticmethod
def check_service_response(url: str) -> bool:
    try:
        with get_legacy_session().get(url=url, verify=False) as resp:
            if resp.status_code == 200 and "Service" in resp.text:
                return True
    except requests.RequestException:
        return False
        
class AddOGCService:
    @staticmethod
    def detect_service_type(url: str, services: List[str]) -> None or str:
        for service in services:
            if service.casefold() in linkifikatormodel2:
                capabilities_url = f"{url}{'' if '?' in url else f'?service={service}&request=GetCapabilities'}"
                if check_service_response(capabilities_url):
                    return service
        for service in services:
            capabilities_url = f"{url}{'' if '?' in url else f'?service={service}&request=GetCapabilities'}"
            if check_service_response(capabilities_url):
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

def check_internet_connection():
    try:
        resp = get_legacy_session().get(url='https://uldk.gugik.gov.pl/', verify=False)
        print("posiadasz polaczenie z internetem")
        return resp.status_code == 200
    except requests.exceptions.Timeout:
        return False
    except ConnectionError:
        return False


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

    def get_services_wfc_wcs_by_teryt(self, unit_type: str, teryt: str) -> Dict:
        return self.get_wfs_wcs_services(f'{EZIUDP_URL}?teryt={teryt}&rodzaj={unit_type}')

    def get_servives_wms_wmts_dict_for_pl(self) -> Dict:
        return self.get_wms_wmts_services(f'{EZIUDP_URL}?teryt=PL')

    def get_servives_wfs_wcs_dict_for_pl(self) -> Dict:
        return self.get_wfs_wcs_services(f'{EZIUDP_URL}?teryt=PL')
    



def fill_services_table(self) -> None:
        dataset_dict = self.get_services_dict()
        for service_name, service_url in dataset_dict.items():
            urls = service_url if isinstance(service_url, list) else [service_url]
            for url in urls:
                row = [
                    QStandardItem(service_name),
                    QStandardItem(url),
                ]
                self.model.appendRow(row)
        self.services_table.setModel(self.model)


from baza_linkow import linkifikacja,linkifikatormodel2
serwisy = linkifikacja

# def add_service(x):
#         services = ['WFS', 'WCS','WMTS', 'WMS']
#         service_type = AddOGCService.detect_service_type(serwisy[x], services)
#         if service_type:
#             success = 1
#         else:
#             success = 0
        
#         return success



def add_service_v2(x):
        try:
            selected_url = serwisy[x]
        except IndexError:
            selected_url = serwisy[x-1]
        services = ['WFS','WCS','WMTS','WMS']
        service_type = AddOGCService.detect_service_type(selected_url, services)
        if service_type:
            success = 1
        else:
            success = 0
        return success




