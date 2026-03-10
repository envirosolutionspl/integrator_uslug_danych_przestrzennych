from qgis.core import Qgis, QgsMessageLog, QgsNetworkAccessManager, QgsBlockingNetworkRequest
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkAccessManager
from qgis.PyQt.QtCore import QUrl

from . import PLUGIN_NAME
from .constants import ENCODING_SYSTEM


class QtCompat:
    @staticmethod
    def getEnum(parent, enum_class, value):
        """Rozwiązanie enumu Qt - próbuje najpierw scoped enum Qt6, a potem Qt5."""
        scoped = getattr(parent, enum_class, None)
        if scoped is not None:
            return getattr(scoped, value)
        return getattr(parent, value)

    @staticmethod
    def execDialog(dialog):
        """Wywołanie exec na QDialog, obsługa różnicy między Qt5 (exec_) a Qt6 (exec)."""
        if hasattr(dialog, 'exec'):
            return dialog.exec()
        return dialog.exec_()

    @staticmethod
    def getMessageBoxIcon(icon='Information'):
        """Zwraca ikonę QMessageBox (Qt5/Qt6 compatible)."""
        from qgis.PyQt.QtWidgets import QMessageBox
        return QtCompat.getEnum(QMessageBox, 'Icon', icon)


class MessageUtils:
    @staticmethod
    def pushSuccess(iface, message: str) -> None:
        iface.messageBar().pushMessage(
            "Sukces:",
            message,
            level=Qgis.Success,
            duration=10
        )


    @staticmethod
    def pushInfo(iface, message: str) -> None:
        iface.messageBar().pushMessage(
            "Informacja:",
            message,
            level=Qgis.Info,
            duration=10
        )


    @staticmethod
    def pushWarning(iface, message: str) -> None:
        iface.messageBar().pushMessage(
            "Ostrzeżenie:",
            message,
            level=Qgis.Warning,
            duration=10
        )


    @staticmethod
    def pushCritical(iface, message: str) -> None:
        iface.messageBar().pushMessage(
            "Błąd:",
            message,
            level=Qgis.Critical,
            duration=10
        )


    @staticmethod
    def logSuccess(message: str) -> None:
        QgsMessageLog.logMessage(
            message,
            tag=PLUGIN_NAME,
            level=Qgis.Success
        )


    @staticmethod
    def logInfo(message: str) -> None:
        QgsMessageLog.logMessage(
            message,
            tag=PLUGIN_NAME,
            level=Qgis.Info
        )


    @staticmethod
    def logWarning(message: str) -> None:
        QgsMessageLog.logMessage(
            message,
            tag=PLUGIN_NAME,
            level=Qgis.Warning
        )


    @staticmethod
    def logCritical(message: str) -> None:
        QgsMessageLog.logMessage(
            message,
            tag=PLUGIN_NAME,
            level=Qgis.Critical
        )


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
