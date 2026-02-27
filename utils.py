from qgis.core import Qgis, QgsMessageLog

from . import PLUGIN_NAME


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
