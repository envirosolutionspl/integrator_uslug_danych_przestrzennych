from typing import Dict

import requests
from lxml import html

from ..constants import EZIUDP_URL


class EziudpServicesFetcher:
    @staticmethod
    def get_services_dict(url: str, idx: int) -> Dict:
        services = {}
        response = requests.get(url)
        if response.status_code != 200:
            return services
        tree = html.fromstring(response.content)
        table = tree.xpath('//table[contains(@class, "table sortable")]')
        if not table:
            return services
        rows = table[0].xpath('.//tr[position()>1]')
        for row in rows:
            columns = row.xpath('.//td')
            if len(columns) >= 6:
                dataset_name = columns[2].text_content().strip()
                view_service = columns[idx]
                link_tag = view_service.xpath('.//a')
                if link_tag:
                    link = link_tag[0].attrib.get('href')
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


