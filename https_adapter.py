import warnings

import requests
import urllib3
import ssl

from urllib3.exceptions import InsecureRequestWarning


class CustomHttpAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, ssl_context=self.ssl_context)


def get_legacy_session():
    warnings.filterwarnings("ignore", category=ResourceWarning)
    warnings.filterwarnings("ignore", category=InsecureRequestWarning)
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    session = requests.session()
    session.mount('https://', CustomHttpAdapter(ctx))
    session.verify = False
    return session
