DICTIONARY_WOJ_URL = 'http://mapy.geoportal.gov.pl/wss/service/SLN/guest/sln/woj.json'
DICTIONARY_POW_URL = 'http://mapy.geoportal.gov.pl/wss/service/SLN/guest/sln/pow/PL.PZGIK.200/'
DICTIONARY_GM_URL = 'http://mapy.geoportal.gov.pl/wss/service/SLN/guest/sln/gmi/PL.PZGIK.200/'

ULDK_GMINA_DICT_URL = 'https://uldk.gugik.gov.pl/service.php?obiekt=gmina&wynik=gmina,teryt&teryt='
ULDK_POWIAT_DICT_URL = 'https://uldk.gugik.gov.pl/service.php?obiekt=powiat&wynik=powiat,teryt&teryt='
ULDK_WOJEWODZTWO_DICT_URL = 'https://uldk.gugik.gov.pl/service.php?obiekt=wojewodztwo&wynik=wojewodztwo,teryt'

GEOPORTAL_WMS_WMTS_URL = 'https://www.geoportal.gov.pl/pl/usluga/uslugi-przegladania-wms-i-wmts/'
GEOPORTAL_WFS_URL = 'https://www.geoportal.gov.pl/pl/usluga/uslugi-pobierania-wfs/'
GEOPORTAL_WCS_URL = 'https://www.geoportal.gov.pl/pl/usluga/uslugi-pobierania-wcs/'

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

ADMINISTRATIVE_UNITS_OBJECTS = {
    'wojewodztwo_combo': ('get_powiat_by_teryt', 'powiat_combo'),
    'powiat_combo': ('get_gmina_by_teryt', 'gmina_combo'),
}

RADIOBUTTONS_UNITS = [
    'kraj_rb',
    'woj_rb',
    'pow_rb',
    'gmi_rb',
]

RADIOBUTTONS_SERVICES = [
    'wms_rdbtn',
    'wfs_rdbtn',
]

COMBOBOX_RADIOBUTTON_LINK = {
    'wojewodztwo_combo': 'woj_rb',
    'powiat_combo': 'pow_rb',
    'gmina_combo': 'gmi_rb',
}

RADIOBUTTON_COMBOBOX_LINK = {COMBOBOX_RADIOBUTTON_LINK[x]: x for x in COMBOBOX_RADIOBUTTON_LINK}

RADIOBUTTONS_TYPES_LINK = {
    'woj_rb': 'wojewodztwa',
    'pow_rb': 'powiaty',
    'gmi_rb': 'gminy',
}

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

