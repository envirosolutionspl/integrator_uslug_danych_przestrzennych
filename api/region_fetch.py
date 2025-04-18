from ..constants import ULDK_GMINA_DICT_URL, ULDK_POWIAT_DICT_URL, ULDK_WOJEWODZTWO_DICT_URL
from ..https_adapter import get_legacy_session


class RegionFetch:
    def __init__(self, teryt=None):
        self.wojewodztwo_dict = self.__fetch_wojewodztwo_dict(teryt)
        self.powiat_dict = self.get_powiat_by_teryt(teryt)
        self.gmina_dict = self.get_gmina_by_teryt(teryt)

    @staticmethod
    def fetch_unit_dict(url, teryt):
        unit_dict = {}
        if teryt:
            url = url+teryt
        with get_legacy_session().get(url=url, verify=False) as resp:
            resp_text = resp.text.strip().split('\n')
            if not resp_text:
                return
            for el in resp_text[1:]:
                split = el.split('|')
                unit_dict[split[1]] = split[0]
        return unit_dict

    def __fetch_wojewodztwo_dict(self, teryt):
        return self.fetch_unit_dict(ULDK_WOJEWODZTWO_DICT_URL, teryt)

    def get_powiat_by_teryt(self, teryt):
        return self.fetch_unit_dict(ULDK_POWIAT_DICT_URL, teryt)

    def get_gmina_by_teryt(self, teryt):
        return self.fetch_unit_dict(ULDK_GMINA_DICT_URL, teryt)

