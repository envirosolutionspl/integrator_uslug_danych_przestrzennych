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
 *       email                : gis@envirosolutions.pl                     *
 *       git sha              : $Format:%H$                                *
 ***************************************************************************/
"""
import os
import sys
from typing import Dict, List

from qgis.PyQt import QtWidgets
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QSortFilterProxyModel, Qt
from qgis.PyQt.QtGui import QShowEvent, QStandardItem, QStandardItemModel
from .modules.content_manager import ContentManager
from .constants import RADIOBUTTONS_SERVICES
from .utils import QtCompat, SingleTaskManager

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'integrator_uslug_danych_przestrzennych_dialog_base.ui'))

class IntegratorUslugPrzestrzennychDialog(QtWidgets.QDialog, FORM_CLASS):

    def __init__(self, parent=None):
        super(IntegratorUslugPrzestrzennychDialog, self).__init__(parent)
        self.setupUi(self)
        self.qt_compat = QtCompat()
        
        self.content_manager = ContentManager(self)
        self.content_manager.setTableRefreshFunction(self.setupTable)
        self.serv_rows = []
        self.table_setup_task = SingleTaskManager(self._fetchServices, self._finishTableSetup)
        self.plugin_name = ''

        self.setupSignals()

        # Inicjacja tabeli 
        self.model = QStandardItemModel()
        self.configureTableHeader()
        self.setupSearch()
        self.setupTable()

    def configureTableHeader(self) -> None:
        " Wstępna konfiguracja tabeli "

        # QtCompat
        resize_interactive = self.qt_compat.getEnum(QtWidgets.QHeaderView, 'ResizeMode', 'Interactive')
        ascending = self.qt_compat.getEnum(Qt, 'SortOrder', 'AscendingOrder')
        align_center = self.qt_compat.getEnum(Qt, 'AlignmentFlag', 'AlignCenter')

        # Inicjacja modelu tabeli
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['', ''])
        self.services_table.setModel(self.model)

        # Ustawienia poziome
        h_header = self.services_table.horizontalHeader()
        h_header.setSectionResizeMode(0, resize_interactive)
        h_header.setSectionResizeMode(1, resize_interactive)
        h_header.setSortIndicator(0, ascending)

        # Ustawienia pionowe
        v_header = self.services_table.verticalHeader()
        v_header.setDefaultSectionSize(14)
        v_header.setDefaultAlignment(align_center)

        self.services_table.setColumnWidth(0, 400)
        self.services_table.setColumnWidth(1, 500)
        self.services_table.setSortingEnabled(True)

    def setupSearch(self) -> None:
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterKeyColumn(0)
        self.services_table.setModel(self.proxy_model)

    def setupDialog(self, plugin_name, plugin_version) -> None:
        self.img_main.setMargin(9)
        self.setWindowTitle('%s %s' % (plugin_name, plugin_version))
        self.lbl_pluginVersion.setText('%s %s' % (plugin_name, plugin_version))
        self.plugin_name = plugin_name

    # =============================
    # Fukcje obsługujące sygnały

    def setupSignals(self) -> None:
        for obj in RADIOBUTTONS_SERVICES:
            widget_obj = getattr(self, obj)
            widget_obj.toggled.connect(self.setupTable)
        self.search_lineedit.textChanged.connect(self.applySearchFilter)
        self.add_btn.clicked.connect(self.addService)

    def setupTable(self) -> None:
        if self.content_manager.isStandaloneFetchTaskRunning() and not self.content_manager.isStandaloneServicesCacheReady():
            self.pushMessageOverTable(" Aktualizacja usług...","Pobieranie danych.")
            return
        if self.table_setup_task.isRunning():
            return
        self.setEnabledRadiobuttons(False)
        self.pushMessageOverTable(" Aktualizacja usług...","Pobieranie")
        if not self.table_setup_task.run(): # SingleTaskManager(self.fetchServices, self.finishTableSetup)
            self.pushMessageOverTable(" Aktualizacja usług...","Nieoczekiwany błąd.")

    def _fetchServices(self) -> None:
        self.serv_rows = self.getServicesRows()

    def _finishTableSetup(self) -> None:
        self.fillServicesTable(self.serv_rows)
        self.applySearchFilter(self.search_lineedit.text())
        self.setEnabledRadiobuttons(True)

    def applySearchFilter(self, text: str) -> None:
        case_insensitive = self.qt_compat.getEnum(Qt, 'CaseSensitivity', 'CaseInsensitive')
        self.proxy_model.setFilterCaseSensitivity(case_insensitive)
        self.proxy_model.setFilterFixedString(text)

    def addService(self):

        # Blokowanie elementów okna
        self.setEnabledRadiobuttons(False)
        self.setEnabledTable(False)
        
        # Pobranie danych z tabeli i dodanie usług do mapy
        proxy_model = self.services_table.model()
        selected_indexes = self.services_table.selectionModel().selectedRows()
        selected_service_type = self.getSelectedServiceType()
        self.content_manager.addServiceFromSelection(proxy_model, selected_indexes, selected_service_type)

        # Odblokowanie elementów okna 
        self.setEnabledRadiobuttons(True)
        self.setEnabledTable(True)
   
    # =============================
    # Fukcje obsługujące elementy okna

    def fillServicesTable(self, service_rows: List = []) -> None:

        # Oczyszczenie tablicy
        row_count = self.model.rowCount()
        if row_count > 0:
            self.model.removeRows(0, row_count)

        # Wypełnienie tablicy
        self.model.setHorizontalHeaderLabels(['Nazwa usługi', 'Adres usługi'])
        for service_row in service_rows:
            row = [
                QStandardItem(service_row['dataset_name']),
                QStandardItem(service_row['url']),
            ]
            self.model.appendRow(row)
        ascending = self.qt_compat.getEnum(Qt, 'SortOrder', 'AscendingOrder')
        self.model.sort(0, ascending)

    def pushMessageOverTable(self, message : str, status : str = '') -> None:
        " Czyści tabelę i wykorzysuje pierwsze pole jako miejsce na komunikat i opcjonalnie status "

        # Oczyszczenie tablicy
        row_count = self.model.rowCount()
        if row_count > 0:
            self.model.removeRows(0, row_count)

        # Wstawienie komunikatu
        self.model.setHorizontalHeaderLabels(['Komunikat', 'Status'])
        row = [
                QStandardItem(message),
                QStandardItem(status)
            ]
        self.model.appendRow(row)

    def setEnabledRadiobuttons(self, is_enabled = True):
        for obj in RADIOBUTTONS_SERVICES:
            widget_obj = getattr(self, obj)
            widget_obj.setEnabled(is_enabled)

    def setEnabledTable(self, is_enabled = True):
        self.services_table.setEnabled(is_enabled)

    def getSelectedServiceType(self) -> str:
        if self.wmts_rdbtn.isChecked():
            return 'WMTS'
        if self.wcs_rdbtn.isChecked():
            return 'WCS'
        if self.wfs_rdbtn.isChecked():
            return 'WFS'
        return 'WMS'

    def getServicesRows(self) -> List[Dict[str, str]]:
        return self.content_manager.getCountryUrlsByServiceType(self.getSelectedServiceType())
    
    # =============================
    # Deklaracja funkcji dziedziczonych

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.content_manager.servicesCacheInit()
        self.setupTable()
        self.setEnabledRadiobuttons(True)
        self.setEnabledTable(True)
        self.wms_rdbtn.setFocus()

    def closeEvent(self, event: QShowEvent) -> None:
        event.accept()
        self.accept()
