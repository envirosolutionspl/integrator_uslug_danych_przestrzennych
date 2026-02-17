import re
from typing import Dict

from lxml import html

from ..https_adapter import NetworkManager
from ..constants import (
    GEOPORTAL_WMS_WMTS_URL,
    GEOPORTAL_WFS_URL,
    GEOPORTAL_WCS_URL
)


class GeoportalServicesFetcher:
    def __init__(self):
        self.manager = NetworkManager()

    def get_services_dict(self, url: str) -> Dict:
        services = {}
        result = self.manager.getSync(url)
        if not result:
            return services
        tree = html.fromstring(result)
        for table in tree.xpath('//table'):
            for row in table.xpath('.//tr[position()>1]'):
                columns = row.xpath('.//td')
                if len(columns) >= 4:
                    service_name = columns[1].text_content().strip()
                    link_tag = columns[3].xpath('.//a')
                    if link_tag and 'href' in link_tag[0].attrib:
                        service_url = link_tag[0].attrib['href']
                        services[re.sub(r"\s+", " ", service_name)] = service_url.strip()
        return services

    def get_wms_wmts_services(self) -> Dict:
        return self.get_services_dict(GEOPORTAL_WMS_WMTS_URL)

    def get_wfs_wcs_services(self) -> Dict:
        return {**self.get_services_dict(GEOPORTAL_WFS_URL), **self.get_services_dict(GEOPORTAL_WCS_URL)}
