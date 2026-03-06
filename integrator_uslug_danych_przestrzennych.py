# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QToolBar

from . import PLUGIN_NAME as pluginName
from . import PLUGIN_VERSION as pluginVersion
from .api.add_service import AddOGCService
from .resources import *  # noqa: F403
from .utils import QtCompat
from .integrator_uslug_danych_przestrzennych_dialog import IntegratorUslugPrzestrzennychDialog
import os.path


class IntegratorUslugPrzestrzennych:
    def __init__(self, iface):
        self.iface = iface
        self.pluginDir = os.path.dirname(__file__)

        locale = QSettings().value('locale/userLocale')[0:2]
        localePath = os.path.join(self.pluginDir, 'i18n', 'IntegratorUslugPrzestrzennych_{}.qm'.format(locale))

        if os.path.exists(localePath):
            self.translator = QTranslator()
            self.translator.load(localePath)
            QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr(u'&EnviroSolutions')

        self.toolbar = self.iface.mainWindow().findChild(QToolBar, 'EnviroSolutions')
        if not self.toolbar:
            self.toolbar = self.iface.addToolBar(u'EnviroSolutions')
            self.toolbar.setObjectName(u'EnviroSolutions')

        self.firstStart = None
        self.qtCompat = QtCompat()

    def tr(self, message):
        return QCoreApplication.translate('IntegratorUslugPrzestrzennych', message)

    def addAction(
        self,
        iconPath,
        text,
        callback,
        enabledFlag=True,
        addToMenu=True,
        addToToolbar=True,
        statusTip=None,
        whatsThis=None,
        parent=None,
    ):
        icon = QIcon(iconPath)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabledFlag)

        if statusTip is not None:
            action.setStatusTip(statusTip)

        if whatsThis is not None:
            action.setWhatsThis(whatsThis)

        if addToToolbar:
            self.toolbar.addAction(action)

        if addToMenu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initGui(self):
        self.dlg = IntegratorUslugPrzestrzennychDialog()
        self.setupDialog()

        iconPath = os.path.join(self.pluginDir, 'images', 'icon.svg')
        self.addAction(
            iconPath,
            text=self.tr(pluginName),
            callback=self.run,
            parent=self.iface.mainWindow(),
        )

        self.firstStart = True

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&EnviroSolutions'), action)
            self.toolbar.removeAction(action)

    def addService(self) -> None:
        successfullyAdd = {}
        selectedUrls = self.dlg.getSelectedServicesUrls()
        for name, url in selectedUrls.items():
            services = ['WFS', 'WCS'] if self.dlg.wfs_rdbtn.isChecked() else ['WMTS', 'WMS']
            serviceType = AddOGCService.detectServiceType(url, services)
            if serviceType:
                addLayer = AddOGCService.addService(url, serviceType)
                successfullyAdd[name] = addLayer
            else:
                successfullyAdd[name] = False

        infoIcon = self.qtCompat.getMessageBoxIcon('Information')
        msgbox = QMessageBox(
            infoIcon,
            'Informacja',
            '\n'.join(
                f'Dodano usluge {key}' if value else f'Nie dodano uslugi {key}'
                for key, value in successfullyAdd.items()
            ),
        )
        self.qtCompat.execDialog(msgbox)

    def setupDialog(self) -> None:
        self.dlg.add_btn.clicked.connect(self.addService)

    def run(self):
        if self.firstStart:
            self.firstStart = False
            self.dlg.setWindowTitle('%s %s' % (pluginName, pluginVersion))
            self.dlg.lbl_pluginVersion.setText('%s %s' % (pluginName, pluginVersion))

        self.dlg.show()
        result = self.qtCompat.execDialog(self.dlg)
        if result:
            pass


