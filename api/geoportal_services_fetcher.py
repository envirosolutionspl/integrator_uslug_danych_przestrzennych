from typing import Dict

import requests
from bs4 import BeautifulSoup

from ..constants import (
    GEOPORTAL_WMS_WMTS_URL,
    GEOPORTAL_WFS_URL,
    GEOPORTAL_WCS_URL
)


class GeoportalServicesFetcher:
    @staticmethod
    def get_services_dict(url: str) -> Dict:
        services = {}
        response = requests.get(url)
        if response.status_code != 200:
            return services
        soup = BeautifulSoup(response.content, 'html.parser')
        for table in soup.find_all('table'):
            for row in table.find_all('tr')[1:]:
                columns = row.find_all('td')
                if len(columns) >= 4:
                    service_name = columns[1].get_text(strip=True)
                    link_tag = columns[3].find('a')
                    if link_tag and 'href' in link_tag.attrs:
                        service_url = link_tag['href']
                        services[service_name] = service_url
        return services

    def get_wms_wmts_services(self) -> Dict:
        return self.get_services_dict(GEOPORTAL_WMS_WMTS_URL)

    def get_wfs_wcs_services(self) -> Dict:
        return {**self.get_services_dict(GEOPORTAL_WFS_URL), **self.get_services_dict(GEOPORTAL_WCS_URL)}




