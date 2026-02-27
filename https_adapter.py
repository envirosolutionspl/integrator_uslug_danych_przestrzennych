from qgis.core import QgsNetworkAccessManager, QgsBlockingNetworkRequest
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkAccessManager
from qgis.PyQt.QtCore import QUrl


class NetworkManager:

    def __init__(self):
        self.manager = QNetworkAccessManager()
        self.manager.setProxy(QgsNetworkAccessManager.instance().proxy())

    def getRequest(self, url):
        """Synchronous GET request. Returns decoded string or None on error."""
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

        return bytes(raw_data).decode('utf-8')
