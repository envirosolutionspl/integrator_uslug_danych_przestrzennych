from qgis.core import QgsNetworkAccessManager, QgsBlockingNetworkRequest
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkAccessManager
from qgis.PyQt.QtCore import QUrl
from .constants import ENCODING_SYSTEM

class NetworkManager:

    def __init__(self):
        self.manager = QNetworkAccessManager()
        self.manager.setProxy(QgsNetworkAccessManager.instance().proxy())

    def getRequest(self, url):
        """Synchroniczna odpowiedź requestu. Zwraca string lub None w przypadku błędu."""
        if isinstance(url, str):
            url = QUrl(url)
        request = QNetworkRequest(url)

        blocking_request = QgsBlockingNetworkRequest()
        error_code = blocking_request.get(request)

        if error_code != QgsBlockingNetworkRequest.NoError:
            return None

        reply = blocking_request.reply()
        raw_data = reply.content()
        if len(raw_data) == 0:
            return None

        return bytes(raw_data).decode(ENCODING_SYSTEM)
