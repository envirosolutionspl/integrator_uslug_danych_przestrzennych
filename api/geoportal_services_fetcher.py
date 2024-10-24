from typing import Dict

import requests
from lxml import html

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
        tree = html.fromstring(response.content)
        for table in tree.xpath('//table'):
            for row in table.xpath('.//tr[position()>1]'):
                columns = row.xpath('.//td')
                if len(columns) >= 4:
                    service_name = columns[1].text_content().strip()
                    link_tag = columns[3].xpath('.//a')
                    if link_tag and 'href' in link_tag[0].attrib:
                        service_url = link_tag[0].attrib['href']
                        services[service_name] = service_url
        return services

    def get_wms_wmts_services(self) -> Dict:
        return self.get_services_dict(GEOPORTAL_WMS_WMTS_URL)

    def get_wfs_wcs_services(self) -> Dict:
        return {**self.get_services_dict(GEOPORTAL_WFS_URL), **self.get_services_dict(GEOPORTAL_WCS_URL)}




