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

ADMINISTRATIVE_UNITS_OBJECTS = {
    'wojewodztwo_combo': ('get_powiat_by_teryt', 'powiat_combo'),
    'powiat_combo': ('get_gmina_by_teryt', 'gmina_combo'),
}

CHECKBOXES = [
    'kraj_check',
    'woj_check',
    'pow_check',
    'gmi_check',
]

RADIOBUTTONS = [
    'wms_rdbtn',
    'wfs_rdbtn',
]

CHECKBOX_COMBOBOX_LINK = {
    'wojewodztwo_combo': 'woj_check',
    'powiat_combo': 'pow_check',
    'gmina_combo': 'gmi_check',
}

CHECKBOX_TYPES_LINK = {
    'woj_check': 'wojewodztwa',
    'pow_check': 'powiaty',
    'gmi_check': 'gminy',
}