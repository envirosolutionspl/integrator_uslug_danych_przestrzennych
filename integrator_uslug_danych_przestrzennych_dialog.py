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
import os
import sys
from typing import Dict, List

from qgis.PyQt import QtWidgets
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QTableView
from qgis.PyQt.QtCore import QSortFilterProxyModel, Qt
from qgis.PyQt.QtGui import QShowEvent, QStandardItem, QStandardItemModel
from .modules.content_manager import ContentManager
from .constants import RADIOBUTTONS_SERVICES, REST_API_CONNECTION_CHECK_URL
from .utils import QtCompat, SingleTaskManager, MessageUtils, ServiceAPI

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'integrator_uslug_danych_przestrzennych_dialog_base.ui'))

class IntegratorUslugPrzestrzennychDialog(QtWidgets.QDialog, FORM_CLASS):

    is_window_shown = False

    def __init__(self, parent=None):
        super(IntegratorUslugPrzestrzennychDialog, self).__init__(parent)
        self.setupUi(self)
        self.qt_compat = QtCompat()
        
        self.content_manager = ContentManager(self)
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
        """Wstępna konfiguracja tabeli"""

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
        self.services_table.setSelectionBehavior(self.qt_compat.getEnum(QTableView, 'SelectionBehavior', 'SelectRows'))
        self.services_table.setSelectionMode(self.qt_compat.getEnum(QTableView, 'SelectionMode', 'MultiSelection'))

    def setupSearch(self) -> None:
        """Konfiguracja modelu proxy dla pola wyszukiwania"""
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterKeyColumn(0)
        self.services_table.setModel(self.proxy_model)

    def setupDialog(self, plugin_name, plugin_version) -> None:
        """Ustawienie podstawowych danych okna dialogowego"""
        self.img_main.setMargin(9)
        self.setWindowTitle('%s %s' % (plugin_name, plugin_version))
        self.lbl_pluginVersion.setText('%s %s' % (plugin_name, plugin_version))
        self.plugin_name = plugin_name

    # =============================
    # Fukcje obsługujące sygnały

    def setupSignals(self) -> None:
        """Ustawienie odbiorców sygnałów emitowanych przez okno dialogowe"""
        for obj in RADIOBUTTONS_SERVICES:
            widget_obj = getattr(self, obj)
            widget_obj.toggled.connect(self.setupTable)
        self.search_lineedit.textChanged.connect(self.applySearchFilter)
        self.add_btn.clicked.connect(self.addService)

    def setupTable(self) -> None:
        """Przeprowadza aktualizację zawartości tabeli."""
        # Zapobiega wyzwalaniu funkcji podczas inicjacji QGIS (ta funkcja wyzwalana jest sygnałem)
        if not self.is_window_shown:
            return
        
        # Pobieranie danych do tabeli
        self.setEnabledRadiobuttons(False)
        self.pushMessageOverTable(" Aktualizacja usług...","Pobieranie")

        # Ponowna próba pobrania danych z API, jeśli poprzednia się nie powiodła
        if len(self.content_manager.getCountryServicesCache()) == 0:
            if not ServiceAPI().checkInternetConnection(REST_API_CONNECTION_CHECK_URL):
                self.pushMessageOverTable(" Brak dostęu do usług...","Błąd połączenia internetowego")
                self.setEnabledRadiobuttons(True)
                return
            else:
                if not self.content_manager.servicesCacheInit():
                    self.setEnabledRadiobuttons(True)
                    return
        
        if not self.table_setup_task.run(): # SingleTaskManager(self.fetchServices, self.finishTableSetup)
            self.pushMessageOverTable(" Aktualizacja usług...","Nieoczekiwany błąd.")

    def _fetchServices(self) -> None:
        """Wątek odpowiedzialny za pobranie danych do tabeli"""
        self.serv_rows = self.getServicesRows()

    def _finishTableSetup(self) -> None:
        """Finalizacja wątka odpowiedzialnego za pobranie danych do tabeli"""
        self.fillServicesTable(self.serv_rows)
        self.applySearchFilter(self.search_lineedit.text())
        self.setEnabledRadiobuttons(True)

    def applySearchFilter(self, text: str) -> None:
        """Zastosowanie filtrów wyszukiwania do tabeli"""
        case_insensitive = self.qt_compat.getEnum(Qt, 'CaseSensitivity', 'CaseInsensitive')
        self.proxy_model.setFilterCaseSensitivity(case_insensitive)
        self.proxy_model.setFilterFixedString(text)

    def addService(self):
        """Funcja pobiera nazwy usług i linki wybrane w tabeli i dodaje usługi do projektu QGIS"""
        # Blokowanie elementów okna
        self.setEnabledRadiobuttons(False)
        self.setEnabledTable(False)

        # Sprawdzanie połaczenia internetowego
        try:
            if ServiceAPI().checkInternetConnection():

                # Pobranie danych z tabeli i dodanie usług do mapy
                proxy_model = self.services_table.model()
                selected_indexes = self.services_table.selectionModel().selectedRows()
                selected_service_type = self.getSelectedServiceType()
                self.content_manager.addServiceFromSelection(proxy_model, selected_indexes, selected_service_type)
                
            else:
                MessageUtils.pushMessageBoxWarning(
                    self,
                    'Ostrzeżenie',
                    'Brak połączenia internetowego.\nWtyczka nie będzie funkcjonować poprawnie.\nNie można dodać usług.',
                )
        finally:
            # Odblokowanie elementów okna 
            self.setEnabledRadiobuttons(True)
            self.setEnabledTable(True)

    # =============================
    # Fukcje obsługujące elementy okna

    def fillServicesTable(self, service_rows: List = []) -> None:
        """Czyści tabelę i wypełnia na nowo danymi"""
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
        """Czyści tabelę i wykorzysuje pierwsze pole jako miejsce na komunikat i opcjonalnie status"""
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
        """Ustawia dostępność radiobutton'ów"""
        for obj in RADIOBUTTONS_SERVICES:
            widget_obj = getattr(self, obj)
            widget_obj.setEnabled(is_enabled)

    def setEnabledTable(self, is_enabled = True):
        """Ustawia dostępność tabeli"""
        self.services_table.setEnabled(is_enabled)

    def getSelectedServiceType(self) -> str:
        """Podaje aktualnie wybrany na radiobutton'ach typ usługi"""
        if self.wmts_rdbtn.isChecked():
            return 'WMTS'
        if self.wcs_rdbtn.isChecked():
            return 'WCS'
        if self.wfs_rdbtn.isChecked():
            return 'WFS'
        return 'WMS'

    def getServicesRows(self) -> List[Dict[str, str]]:
        """Pobiera listę usług według wybranego typu usługi"""
        return self.content_manager.getCountryUrlsByServiceType(self.getSelectedServiceType())
    
    # =============================
    # Deklaracja funkcji dziedziczonych

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if not self.is_window_shown:
            if not self.content_manager.servicesCacheInit():
                MessageUtils.pushMessageBoxWarning(
                    self,
                    'Ostrzeżenie',
                    'Brak połączenia internetowego.\nWtyczka nie będzie funkcjonować poprawnie\nNie można pobrać usług.',
                )
            self.is_window_shown = True
        self.setupTable()
        self.setEnabledRadiobuttons(True)
        self.setEnabledTable(True)
        self.wms_rdbtn.setFocus()

    def closeEvent(self, event: QShowEvent) -> None:
        self.is_window_shown = False
        event.accept()
        self.accept()
