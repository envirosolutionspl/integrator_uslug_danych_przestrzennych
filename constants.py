REST_API_BASE_URL = 'https://rest.envirosolutions.pl/integrator'
REST_ENDPOINT_COUNTRY = '/get-country-urls'
RESULT_SERVICE_TAG = 'Service'
ENCODING_SYSTEM = "utf-8"
EZIUDP_URL = 'https://integracja.gugik.gov.pl/eziudp/index.php'

FEED_URL = 'https://qgisfeed.envirosolutions.pl/'

INDUSTRIES = {
    "999": 'Nie wybrano',
    "e": 'Energetyka/OZE',
    "u": 'Urząd',
    "td": 'Transport/Drogi',
    "pg": 'Planowanie/Geodezja',
    "wk": 'WodKan',
    "s": 'Środowisko',
    "rl": 'Rolnictwo/Leśnictwo',
    "tk": 'Telkom',
    "edu": 'Edukacja',
    "i": 'Inne',
    "it": 'IT',
    "n": 'Nieruchomości'
}


RADIOBUTTONS_SERVICES = [
    'wms_rdbtn',
    'wfs_rdbtn',
]

SERVICES_NAMESPACES = {
    'WCS': {
        'wcs': 'http://www.opengis.net/wcs/2.0',
        'ows': 'http://www.opengis.net/ows/2.0'
    },
    'WFS': {
        'wfs': 'http://www.opengis.net/wfs/2.0',
        'ows': 'http://www.opengis.net/ows/1.1'
    },
    'WMS': {
        'wms': 'http://www.opengis.net/wms'
    },
    'WMTS': {
        'wmts': 'http://www.opengis.net/wmts/1.0',
        'ows': 'http://www.opengis.net/ows/1.1'
    },
}

