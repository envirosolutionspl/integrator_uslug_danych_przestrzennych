REST_API_BASE_URL = 'https://rest.envirosolutions.pl/integrator'
REST_ENDPOINT_COUNTRY = '/get-country-urls'
RESULT_SERVICE_TAG = 'Service'

ENCODING_SYSTEM = "utf-8"

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
    'wmts_rdbtn',
    'wcs_rdbtn',
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
# =============================
# Parametry do klasy VersionUtils
# wersja Qt6
QT_VER = {
    6: "6."
}

# =============================
# Parametry do klasy NetworkUtils
# Nagłówek w requests
USER_AGENT_HEADER = "Integrator-QGIS-Client/1.0"
CONNECTION_HEADER = "close"

TIMEOUT_MS = 5000
MAX_ATTEMPTS = 3
CANCEL_CHECK_MS = 500
HTTP_ERROR_THRESHOLD = 400

# Nazwy atrybutów
NETWORK_ATTRS = {
    'HTTP_STATUS': 'HttpStatusCodeAttribute',
    'HTTP_REASON': 'HttpReasonPhraseAttribute',
    'REDIRECT': 'RedirectPolicyAttribute',
    'TIMEOUT': 'TimeoutAttribute'
}

# RedirectPolicy
REDIRECT_POLICY_NAME = 'RedirectPolicy'
REDIRECT_POLICY_NO_LESS_SAFE = 'NoLessSafeRedirectPolicy'
DEFAULT_REDIRECT_POLICY = 1

# Wartości błędów i statusów
ERR_TIMEOUT = 'TimeoutError'
ERR_NONE = 'NoError'
ERR_CANCELED = 'OperationCanceledError'
STATUS_SUCCESS = 'brak_bledow'
STATUS_CANCELED = 'anulowano'

# Komunikaty sieciowe
MSG_DOWNLOAD_CANCELED = "Pobieranie zostało anulowane."
MSG_NETWORK_ERROR = "Błąd sieciowy ({}) dla: {}"
MSG_HTTP_ERROR = "Błąd HTTP {}: {}"
MSG_EMPTY_CONTENT = "Serwer zwrócił pustą zawartość dla: {}"
MSG_TIMEOUT = "Przekroczono czas oczekiwania dla: {}"
MSG_FILE_WRITE_ERROR = "Błąd zapisu do pliku: {}"
MSG_JSON_DECODE_ERROR = "Błąd JSON: {}"
MSG_NO_CONNECTION = "Brak połączenia z internetem."


# =============================
# Parametry do klasy StandaloneUrlsFetcher
SERVICE_TYPES = (
    "wms",
    "wmts",
    "wfs",
    "wcs",
)

TERYT_PL = 'PL'

# =============================
# Parametry do klasy GeoportalServicesFetcher
#GEOPORTAL endpoints
GEOPORTAL_WMS_WMTS_URL = (
    "https://www.geoportal.gov.pl/pl/usluga/uslugi-przegladania-wms-i-wmts/"
)
GEOPORTAL_WFS_URL = "https://www.geoportal.gov.pl/pl/usluga/uslugi-pobierania-wfs/"
GEOPORTAL_WCS_URL = "https://www.geoportal.gov.pl/pl/usluga/uslugi-pobierania-wcs/"

# =============================
# Parametry do klasy
# EZIUDP endpoint
EZIUDP_BASE_URL = "https://integracja.gugik.gov.pl/eziudp/index.php"

# EZIUDP HTML parsing
XPATH_TABLE_SORTABLE = '//table[contains(@class, "table sortable")]'
XPATH_TABLE_ROWS = ".//tr[position()>1]"
XPATH_ROW_COLUMNS = ".//td"
XPATH_LINK_TAG = ".//a"
MIN_COLUMNS_FOR_ROW = 6
DATASET_NAME_COLUMN = 2
WMS_WMTS_COLUMN = 5
WFS_WCS_COLUMN = 6

# EZIUDP fetcher settings
SERVICES_REQUEST_TIMEOUT_SECONDS = 10
EZIUDP_WMS_WMTS_NEEDLES = ("wms", "wmts")
EZIUDP_WFS_WCS_NEEDLES = ("wfs", "wcs")