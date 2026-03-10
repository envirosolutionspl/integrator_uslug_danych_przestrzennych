# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QToolBar

from .api.add_service import AddOGCService
from .utils import QtCompat, MessageUtils, NetworkManager
from .integrator_uslug_danych_przestrzennych_dialog import IntegratorUslugPrzestrzennychDialog
import os.path

from . import PLUGIN_NAME as plugin_name
from . import PLUGIN_VERSION as plugin_version

class IntegratorUslugPrzestrzennych:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.message_utils = MessageUtils()
        self.network_manager = NetworkManager()
        self.ogc_service = AddOGCService(self.network_manager)
        
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', 'IntegratorUslugPrzestrzennych_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr(u'&EnviroSolutions')

        self.toolbar = self.iface.mainWindow().findChild(QToolBar, 'EnviroSolutions')
        if not self.toolbar:
            self.toolbar = self.iface.addToolBar(u'EnviroSolutions')
            self.toolbar.setObjectName(u'EnviroSolutions')

        self.first_start = None
        self.qt_compat = QtCompat()

    def tr(self, message):
        return QCoreApplication.translate('IntegratorUslugPrzestrzennych', message)

    def addAction(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None,
    ):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initGui(self):
        self.dlg = IntegratorUslugPrzestrzennychDialog()
        self.setupDialog()

        icon_path = os.path.join(self.plugin_dir, 'images', 'icon.svg')
        self.addAction(
            icon_path,
            text=self.tr(plugin_name),
            callback=self.run,
            parent=self.iface.mainWindow(),
        )

        self.first_start = True

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&EnviroSolutions'), action)
            self.toolbar.removeAction(action)

    def addService(self) -> None:
        successfully_add = {}
        selected_urls = self.dlg.getSelectedServicesUrls()
        for name, url in selected_urls.items():
            services = ['WFS', 'WCS'] if self.dlg.wfs_rdbtn.isChecked() else ['WMTS', 'WMS']
            service_type = self.ogc_service.detectServiceType(url, services)
            if service_type:
                if_add_layer = self.ogc_service.addService(url, service_type)
                successfully_add[name] = if_add_layer
            else:
                successfully_add[name] = False

        self.message_utils.pushInfo(self.iface, '\n'.join(
            f'Dodano usluge {key}' if value else f'Nie dodano uslugi {key}'
            for key, value in successfully_add.items()
        ))

    def setupDialog(self) -> None:
        self.dlg.add_btn.clicked.connect(self.addService)

    def run(self):
        if self.first_start:
            self.first_start = False
            self.dlg.setWindowTitle('%s %s' % (plugin_name, plugin_version))
            self.dlg.lbl_pluginVersion.setText('%s %s' % (plugin_name, plugin_version))

        self.dlg.show()
        result = self.qt_compat.execDialog(self.dlg)
        if result:
            pass


