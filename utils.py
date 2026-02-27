from qgis.core import Qgis, QgsMessageLog

from . import PLUGIN_NAME


class QtCompat:
    @staticmethod
    def get_enum(parent, enum_class, value):
        """Resolve Qt enum - tries Qt6-style scoped enum first, falls back to Qt5."""
        scoped = getattr(parent, enum_class, None)
        if scoped is not None:
            return getattr(scoped, value)
        return getattr(parent, value)

    @staticmethod
    def exec_dialog(dialog):
        """Call exec on a QDialog, handling Qt5 (exec_) / Qt6 (exec) difference."""
        if hasattr(dialog, 'exec'):
            return dialog.exec()
        return dialog.exec_()


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
