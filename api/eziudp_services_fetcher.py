from typing import Dict

import requests
from bs4 import BeautifulSoup

from ..constants import EZIUDP_URL


class EziudpServicesFetcher:
    @staticmethod
    def get_services_dict(url: str, idx: int) -> Dict:
        services = {}
        response = requests.get(url)
        if response.status_code != 200:
            return services
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'class': 'table sortable'})
        if not table:
            return services
        rows = table.find_all('tr')[1:]
        for row in rows:
            columns = row.find_all('td')
            if len(columns) >= 6:
                dataset_name = columns[2].text.strip()
                view_service = columns[idx]
                if view_service.find('a'):
                    link = view_service.find('a')['href']
                    services[dataset_name] = link
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


