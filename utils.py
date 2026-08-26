# -*- coding: utf-8 -*-
"""
/***************************************************************************
 * Integrator Uslug Danych Przestrzennych                                  *
 *                                 A QGIS plugin                           *
 * Wtyczka umożliwia prezentację danych z serwisów WMS, WMTS, WFS i WCS    *
 * w postaci warstw w QGIS. Wtyczka wykorzystuje dane z Ewidencji Zbiorów  *
 * i Usług oraz strony geoportal.gov.pl                                    *
 * ----------------------------------------------------------------------- *
 *       begin                : 2026-05-28                                 *
 *       copyright            : (C) 2026 by EnviroSolutions Sp. z o.o.     *
 *       email                : office@envirosolutions.pl                  *
 *       git sha              : $Format:%H$                                *
 ***************************************************************************/
"""
from typing import Callable
import json
import os
import time
from functools import partial
import requests
import ssl
import urllib3

from qgis.core import (
    Qgis,
    QgsMessageLog, 
    QgsNetworkAccessManager, 
    QgsBlockingNetworkRequest, 
    QgsTask,
    QgsApplication,
)

from qgis.PyQt.QtWidgets import QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QUrl, QUrlQuery, QEventLoop, QTimer, QT_VERSION_STR
from qgis.PyQt.QtNetwork import QNetworkReply, QNetworkRequest, QNetworkAccessManager

try:
    if urllib3.__version__.startswith("1."):
        from urllib3.util.ssl_ import create_urllib3_context
    else:
        from urllib3.util import create_urllib3_context
except ImportError:
    QMessageBox.critical(
        None,
        "Błąd biblioteki",
        "Wystąpił problem z wersją urllib3. "
        "Wtyczka może nie działać poprawnie.",
    )
    create_urllib3_context = None

from . import PLUGIN_NAME

from .constants import (
    ENCODING_SYSTEM,
    TIMEOUT_MS,
    QT_VER,
    CANCEL_CHECK_MS,
    HTTP_ERROR_THRESHOLD,
    NETWORK_ATTRS,
    ERR_TIMEOUT,
    ERR_NONE,
    ERR_CANCELED,
    REDIRECT_POLICY_NAME,
    REDIRECT_POLICY_NO_LESS_SAFE,
    DEFAULT_REDIRECT_POLICY,
    MAX_ATTEMPTS,
    MSG_NO_CONNECTION,
    MSG_FILE_WRITE_ERROR, 
    MSG_DOWNLOAD_CANCELED, 
    MSG_EMPTY_CONTENT, 
    MSG_JSON_DECODE_ERROR, 
    MSG_HTTP_ERROR, 
    MSG_TIMEOUT, 
    MSG_NETWORK_ERROR,
    EZIUDP_BASE_URL,
    USER_AGENT_HEADER,
    CONNECTION_HEADER,
)

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


class SingleTaskManager:
    """
    Klasa obsługująca z założenia maksymalnie jeden aktywny poboczny wątek. Zapobiega podwójnemu wywołaniu zadania.
    """

    def __init__(self, main_func: Callable = None, on_finish_func: Callable = None, task_name: str = 'processing'):
        """
        :param main_func: Funkcja zadania, która zostanie wyzwolona w poleceniu run()
        :type nazwa_pliku: function
        
        :param on_finish_func: Funkcja, która zostanie wyzwolona po zakończeniu głównego zadania
        :type nazwa_pliku: function

        :param task_name: Nazwa procesu w tle, czasem może wyświetlić się w pasku, więc warto zadeklarować
        :type task_name: str
        """
        self.task_name = task_name
        self.task_instance = None
        self.task_func = main_func
        self.on_finish_func = on_finish_func

    def _task_func(self, task):
        """ Opakowanie dla funkcji wzbogacone o parametr 'task' """
        if self.task_func is not None:
            self.task_func()

    def _on_finish_func(self, exception, value=None):
        """ Opakowanie dla funkcji wzbogacone o parametry 'exceptio' """
        if self.on_finish_func is not None:
            self.on_finish_func()

    def connectMainFunction(self, main_func : Callable) -> bool:
        """
        Podpina funkcję, która będzie uruchamiana w zadaniu.
        
        :param main_func: Funkcja zadania, która zostanie wyzwolona w poleceniu run()
        :type nazwa_pliku: function

        :returns: False, gdy funkcja jest w użyciu. True jeśli pomyślnie podmieniono.
        :rtype: bool
        """
        if self.isRunning():
            return False
        self.task_func = main_func
        return True

    def connectOnFinishFunction(self, on_finish_func : Callable) -> bool:
        """
        Podpina funkcję, która będzie uruchamiana w zadaniu.
        
        :param on_finish_func: Funkcja, która zostanie wyzwolona po zakończeniu głównego zadania
        :type nazwa_pliku: function
        
        :returns: False, gdy funkcja jest w użyciu. True jeśli pomyślnie podmieniono.
        :rtype: bool
        """

        if self.isRunning():
            return False
        self.on_finish_func = on_finish_func
        return True

    def run(self, main_func : Callable = None, on_finish_func : Callable = None) -> bool:
        """
        Rozpoczyna zadanie na podstawie ustawionych funkcji wykonawczych.
        Jeśli nie podano deklaracjifunkcji w parametrze,
        zostaną użyte te, które zostały wcześniej zadeklarowne.

        :param main_func: Funkcja zadania, która zostanie wyzwolona w poleceniu run()
        :type nazwa_pliku: function
        
        :param on_finish_func: Funkcja, która zostanie wyzwolona po zakończeniu głównego zadania
        :type nazwa_pliku: function

        :returns: False, gdy funkcja jest w użyciu lub nie została zadeklarowana. True jeśli pomyślnie uruchomiono.
        :rtype: bool
        """
        if self.isRunning():
            return False
        
        # Aktualizujemy podpięte funckje
        self.task_func = main_func if main_func is not None else self.task_func
        self.on_finish_func = on_finish_func if on_finish_func is not None else self.on_finish_func

        if self.task_func is None:
            return False

        self.task_instance = QgsTask.fromFunction(
            self.task_name,
            self._task_func,
            on_finished=self._on_finish_func,
        )
        QgsApplication.taskManager().addTask(self.task_instance)
        return True
    

    def isRunning(self):
        """
        Sprawdza czy zadanie jest uruchomione.

        :returns: True lub False.
        :rtype: bool
        """
        if self.task_instance is not None and self.task_instance in QgsApplication.taskManager().tasks():
            return True
        return False


class MessageUtils:
    @staticmethod
    def pushMessageBoxCritical(parent, title: str, message: str) -> None:
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QtCompat.getMessageBoxIcon('Critical'))
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QtCompat.getEnum(QMessageBox, 'StandardButton', 'Ok'))
        if hasattr(parent, 'plugin_icon'):
            msg_box.setWindowIcon(QIcon(parent.plugin_icon))
        QtCompat.execDialog(msg_box)

    @staticmethod
    def pushMessageBoxInfo(parent, title: str, message: str) -> None:
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QtCompat.getMessageBoxIcon('Information'))
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QtCompat.getEnum(QMessageBox, 'StandardButton', 'Ok'))
        if hasattr(parent, 'plugin_icon'):
            msg_box.setWindowIcon(QIcon(parent.plugin_icon))
        QtCompat.execDialog(msg_box)

    @staticmethod
    def pushMessageBoxWarning(parent, title: str, message: str) -> None:
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QtCompat.getMessageBoxIcon('Warning'))
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QtCompat.getEnum(QMessageBox, 'StandardButton', 'Ok'))
        if hasattr(parent, 'plugin_icon'):
            msg_box.setWindowIcon(QIcon(parent.plugin_icon))
        QtCompat.execDialog(msg_box)
        
    @staticmethod
    def pushMessageBoxCritical(parent, title: str, message: str) -> None:
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QtCompat.getMessageBoxIcon('Critical'))
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QtCompat.getEnum(QMessageBox, 'StandardButton', 'Ok'))
        if hasattr(parent, 'plugin_icon'):
            msg_box.setWindowIcon(QIcon(parent.plugin_icon))
        QtCompat.execDialog(msg_box)

    @staticmethod
    def pushSuccess(iface, message: str) -> None:
        success = QtCompat.enum(Qgis, 'MessageLevel', 'Success')
        iface.messageBar().pushMessage(
            "Sukces:",
            message,
            level=success,
            duration=10
        )


    @staticmethod
    def pushInfo(iface, message: str) -> None:
        info = QtCompat.getEnum(Qgis, 'MessageLevel', 'Info')
        iface.messageBar().pushMessage(
            "Informacja:",
            message,
            level=info,
            duration=10
        )


    @staticmethod
    def pushWarning(iface, message: str) -> None:
        warning = QtCompat.getEnum(Qgis, 'MessageLevel', 'Warning')
        iface.messageBar().pushMessage(
            "Ostrzeżenie:",
            message,
            level=warning,
            duration=10
        )


    @staticmethod
    def pushCritical(iface, message: str) -> None:
        critical = QtCompat.getEnum(Qgis, 'MessageLevel', 'Critical')
        iface.messageBar().pushMessage(
            "Błąd:",
            message,
            level=critical,
            duration=10
        )


    @staticmethod
    def logSuccess(message: str) -> None:
        success = QtCompat.getEnum(Qgis, 'MessageLevel', 'Success')
        QgsMessageLog.logMessage(
            message,
            tag=PLUGIN_NAME,
            level=success
        )


    @staticmethod
    def logInfo(message: str) -> None:
        info = QtCompat.getEnum(Qgis, 'MessageLevel', 'Info')
        QgsMessageLog.logMessage(
            message,
            tag=PLUGIN_NAME,
            level=info
        )


    @staticmethod
    def logWarning(message: str) -> None:
        warning = QtCompat.getEnum(Qgis, 'MessageLevel', 'Warning')
        QgsMessageLog.logMessage(
            message,
            tag=PLUGIN_NAME,
            level=warning
        )


    @staticmethod
    def logCritical(message: str) -> None:
        critical = QtCompat.getEnum(Qgis, 'MessageLevel', 'Critical')
        QgsMessageLog.logMessage(
            message,
            tag=PLUGIN_NAME,
            level=critical
        )


class LegacySslAdapter(requests.adapters.HTTPAdapter):
    """Adapter dopuszczający stare połączenia SSL"""
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.options |= 0x4  # ssl.OP_LEGACY_SERVER_CONNECT
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

class NetworkUtils:

    def __init__(self):
        self.manager = QNetworkAccessManager()
        self.manager.setProxy(QgsNetworkAccessManager.instance().proxy())
        
        # Wyciszenie ostrzeżeń o braku weryfikacji SSL (InsecureRequestWarning)
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _handleReplyError(self, reply, url_str):
        """Centralna obsługa błędów sieciowych i HTTP"""
        
        error_code = reply.error()
        error_str = reply.errorString()
        
        status_attr = self._getAttributeEnum(NETWORK_ATTRS['HTTP_STATUS'])
        reason_attr = self._getAttributeEnum(NETWORK_ATTRS['HTTP_REASON'])
        timeout_err = self._getErrorEnum(ERR_TIMEOUT)

        http_status = reply.attribute(status_attr)
        http_reason = reply.attribute(reason_attr)
        
        if http_status and http_status >= HTTP_ERROR_THRESHOLD:
            return False, MSG_HTTP_ERROR.format(http_status, http_reason)
        
        if error_code == timeout_err:
            return False, MSG_TIMEOUT.format(url_str)
            
        return False, MSG_NETWORK_ERROR.format(error_str, url_str)

    def _hasErrorOccurred(self, reply):
        """Sprawdza czy wystąpił błąd w odpowiedzi"""
        no_error = self._getErrorEnum(ERR_NONE)
        return reply.error() != no_error

    def _getAttributeEnum(self, attr_name):
        """Pobiera atrybut QNetworkRequest"""
        if VersionUtils.isCompatibleQtVersion(QT_VERSION_STR, 6):
            if hasattr(QNetworkRequest, 'Attribute'):
                val = getattr(QNetworkRequest.Attribute, attr_name, None)
                if val is not None:
                    return val
        return getattr(QNetworkRequest, attr_name, None)

    def _getErrorEnum(self, attr_name):
        """Pobiera kod błędu QNetworkReply"""
        if VersionUtils.isCompatibleQtVersion(QT_VERSION_STR, 6):
            if hasattr(QNetworkReply, 'NetworkError'):
                val = getattr(QNetworkReply.NetworkError, attr_name, None)
                if val is not None:
                    return val
        return getattr(QNetworkReply, attr_name, None)

    def _setAttributes(self, request, timeout_ms):
        """Ustawia atrybuty zapytania"""
        redirect_attr = self._getAttributeEnum(NETWORK_ATTRS['REDIRECT'])
        if redirect_attr is not None:
            redirect_policy_class = getattr(QNetworkRequest, REDIRECT_POLICY_NAME, QNetworkRequest)
            redirect_policy = getattr(redirect_policy_class, REDIRECT_POLICY_NO_LESS_SAFE, DEFAULT_REDIRECT_POLICY)
            request.setAttribute(redirect_attr, redirect_policy)
        
        timeout_attr = self._getAttributeEnum(NETWORK_ATTRS['TIMEOUT'])
        if timeout_attr is not None:
            request.setAttribute(timeout_attr, timeout_ms)
            
    def fetchContent(self, url, params=None, timeout_ms=TIMEOUT_MS):
        q_url = QUrl(url)
        if params:
            query = QUrlQuery()
            for key, value in params.items():
                query.addQueryItem(str(key), str(value))
            q_url.setQuery(query)
            
        request = QNetworkRequest(q_url)
        self._setAttributes(request, timeout_ms)
        
        blocking_request = QgsBlockingNetworkRequest()
        error_code = blocking_request.get(request)
        reply_content = blocking_request.reply()
        
        # Fallback: każda nieudana próba Qt skutkuje próbą przez requests
        no_error = QtCompat.getEnum(QgsBlockingNetworkRequest, 'ErrorCode', 'NoError')
        if error_code != no_error:
            return self._fetchContentWithRequests(url, params, timeout_ms)

        raw_data = reply_content.content()
        if len(raw_data) == 0:
            return False, MSG_EMPTY_CONTENT.format(url)
            
        try:
            data = bytes(raw_data).decode(ENCODING_SYSTEM)
            return True, data
        except UnicodeDecodeError:
            return True, f"BinaryData: {len(raw_data)} bytes"

    def fetchJson(self, url, params=None, timeout_ms=TIMEOUT_MS):
        is_success, result = self.fetchContent(url, params, timeout_ms)
        if not is_success:
            return False, result
        try:
            return True, json.loads(result)
        except json.JSONDecodeError as e:
            return False, MSG_JSON_DECODE_ERROR.format(str(e))
  
    def downloadFile(self, url, dest_path, obj=None, timeout_ms=TIMEOUT_MS):
        request = QNetworkRequest(QUrl(url))
        self._setAttributes(request, timeout_ms)

        dest_dir = os.path.dirname(dest_path)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)

        event_loop = QEventLoop()
        reply = self.manager.get(request)
        try:
            with open(dest_path, 'wb') as f:
                reply.readyRead.connect(partial(self._handleReadyRead, reply, f))
                reply.finished.connect(event_loop.quit)

                self._loopForCancel(obj, reply, event_loop)

                if reply.bytesAvailable() > 0:
                    f.write(reply.readAll().data())
        except IOError as e:
            return False, MSG_FILE_WRITE_ERROR.format(str(e))
            
        status, message = self._finilizeDownload(reply, url)
        
        # Fallback: każda nieudana próba Qt skutkuje próbą przez requests
        if not status:
            return self._downloadFileWithRequests(url, dest_path, obj, timeout_ms)
            
        return status, message

    def _handleReadyRead(self, reply, file):
        if reply.bytesAvailable() > 0:
            file.write(reply.readAll().data())

    def _loopForCancel(self, obj, reply, event_loop):
        cancel_timer = QTimer()
        cancel_timer.timeout.connect(lambda: reply.abort() if (obj and obj.isCanceled()) else None)
        cancel_timer.start(CANCEL_CHECK_MS)
        
        event_loop.exec()

        cancel_timer.stop()
    
    def _finilizeDownload(self, reply, url):
        if self._hasErrorOccurred(reply):
            canceled_error = self._getErrorEnum(ERR_CANCELED)
            if reply.error() == canceled_error:
                reply.deleteLater()
                return False, MSG_DOWNLOAD_CANCELED
            
            error_res = self._handleReplyError(reply, url)
            reply.deleteLater()
            return error_res

        reply.deleteLater()
        return True, True

    # Fallback do requests

    def _getSessionWithLegacySsl(self):
        """Tworzy sesję requests dopuszczającą stare połączenia SSL (legacy renegotiation)"""
        session = requests.Session()
        session.mount("https://", LegacySslAdapter())

        session.headers.update({
            "User-Agent": USER_AGENT_HEADER,
            "Connection": CONNECTION_HEADER,
        })

        # Przekazanie proxy z QGIS
        proxy = self.manager.proxy()
        if proxy.hostName():
            proxy_url = f"http://{proxy.user()}:{proxy.password()}@{proxy.hostName()}:{proxy.port()}" if proxy.user() else f"http://{proxy.hostName()}:{proxy.port()}"
            session.proxies = {"http": proxy_url, "https": proxy_url}
            
        return session


    def _downloadFileWithRequests(self, url, dest_path, obj=None, timeout_ms=TIMEOUT_MS):
        try:
            response = self._requestsGet(url, timeout_ms=timeout_ms, stream=True)

            response.raise_for_status()

            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(8192):

                    if obj and obj.isCanceled():
                        return False, MSG_DOWNLOAD_CANCELED

                    if chunk:
                        f.write(chunk)

            return True, True

        except Exception as e:
            return self._handleRequestsError(e)   

    def _fetchContentWithRequests(self, url, params=None, timeout_ms=TIMEOUT_MS):
        try:
            response = self._requestsGet(url, params=params, timeout_ms=timeout_ms)

            response.raise_for_status()
            return True, response.text

        except Exception as e:
            return self._handleRequestsError(e)

    def _requestsGet(self, url, params=None, timeout_ms=TIMEOUT_MS, stream=False):
        timeout_s = timeout_ms / 1000.0
        session = self._getSessionWithLegacySsl()

        response = session.get(
            url,
            params=params,
            timeout=timeout_s,
            stream=stream,
            verify=False
        )

        return response
    
    def _handleRequestsError(self, e):

        if isinstance(e, requests.exceptions.Timeout):
            return False, "Timeout (requests)"

        if isinstance(e, requests.exceptions.SSLError):
            return False, f"Błąd SSL: {str(e)}"

        if isinstance(e, requests.exceptions.ConnectionError):
            return False, f"Błąd połączenia: {str(e)}"

        if isinstance(e, requests.exceptions.ChunkedEncodingError):
            return False, f"Przerwane pobieranie: {str(e)}"

        if isinstance(e, OSError):
            return False, f"Błąd systemu plików: {str(e)}"

        return False, f"Nieoczekiwany błąd requests: {str(e)}"
   
class ServiceAPI:
    def __init__(self, parent=None):
        if parent:
            self.iface = parent.iface
        else:
            self.iface = None
        self.network_utils = NetworkUtils()


    def getRequest(self, url, params=None):
        attempt = 0
        while attempt <= MAX_ATTEMPTS:
            attempt += 1
            is_success, result = self.network_utils.fetchContent(url, params=params, timeout_ms=TIMEOUT_MS * 2)
            if is_success:
                return True, result
            time.sleep(2)
        return False, "Nieudana próba połączenia"
    

    def checkInternetConnection(self, url=EZIUDP_BASE_URL):
        # próba połączenia z serwerem np. gugik
        is_success, _ = self.network_utils.fetchContent(url, timeout_ms=TIMEOUT_MS)
        if not is_success and self.iface:
            MessageUtils.pushWarning(self.iface, MSG_NO_CONNECTION)
        return is_success

class VersionUtils:

    @staticmethod
    def isCompatibleQtVersion(cur_version, tar_version):
        return cur_version.startswith(QT_VER[tar_version])