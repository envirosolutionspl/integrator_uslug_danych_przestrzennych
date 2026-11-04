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

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 Ten skrypt dodaje wtyczkę do paska narzędziowego.
"""

from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QToolBar
from qgis.core import Qgis, QgsSettings

from .integrator_uslug_danych_przestrzennych_dialog import IntegratorUslugPrzestrzennychDialog
from .utils import QtCompat
from .qgis_feed import QgisFeed, QgisFeedDialog
from .constants import DOCK_START_MAX_RATIO, DOCK_START_WIDTH, INDUSTRIES
import os.path

from . import PLUGIN_NAME as plugin_name
from . import PLUGIN_VERSION as plugin_version


class IntegratorUslugPrzestrzennych:
    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.settings = QgsSettings()
        self.selected_industry = None
        self.feed = None
        self.setupFeed()

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

    def setupFeed(self) -> None:
        if Qgis.QGIS_VERSION_INT < 31000:
            return

        self.selected_industry = self.settings.value('selected_industry', None)
        show_dialog = self.settings.value('showDialog', True, type=bool)

        # wczytywanie branży jeżeli nie jest zgodna z aktualnym słownikiem
        if self.selected_industry not in INDUSTRIES.values():
            self.selected_industry = None
            show_dialog = True

        if self.selected_industry is None and show_dialog:
            self.showBranchSelectionDialog()

        select_indust_session = self.settings.value('selected_industry')

        self.feed = QgisFeed(selected_industry=select_indust_session, plugin_name=plugin_name)
        self.feed.initFeed()

    def showBranchSelectionDialog(self):
        """Wyświetla dialog wyboru branży dla QGIS Feed."""
        dialog = QgisFeedDialog(self.iface.mainWindow())
        dialog.exec()
        self.selected_industry = self.settings.value('selected_industry', None)

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
        self.dlg.setupDialog(plugin_name, plugin_version)

        icon_path = os.path.join(self.plugin_dir, 'images', 'icon.svg')
        self.addAction(
            icon_path,
            text=self.tr(plugin_name),
            callback=self.run,
            parent=self.iface.mainWindow(),
        )

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&EnviroSolutions'), action)
            self.toolbar.removeAction(action)
        self.iface.removeDockWidget(self.dlg)

    def run(self):
        """Pokazuje panel wtyczki - przy pierwszym uruchomieniu dokuje go po prawej stronie okna QGIS."""
        main_window = self.iface.mainWindow()
        first_dock = self.dlg.parentWidget() is not main_window
        if first_dock:
            right_area = QtCompat.getEnum(Qt, 'DockWidgetArea', 'RightDockWidgetArea')
            self.iface.addDockWidget(right_area, self.dlg)
        self.dlg.show()
        self.dlg.raise_()
        if first_dock:
            # szerokość startowa - nie więcej niż część okna QGIS, żeby na małym ekranie nie zabrać mapy
            width = min(DOCK_START_WIDTH, int(main_window.width() * DOCK_START_MAX_RATIO))
            horizontal = QtCompat.getEnum(Qt, 'Orientation', 'Horizontal')
            main_window.resizeDocks([self.dlg], [width], horizontal)
