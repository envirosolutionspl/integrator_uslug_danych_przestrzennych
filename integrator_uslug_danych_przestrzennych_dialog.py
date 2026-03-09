# -*- coding: utf-8 -*-
import os
import sys
from typing import Dict, List

from qgis.PyQt import QtWidgets
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QSortFilterProxyModel, Qt
from qgis.PyQt.QtGui import QShowEvent, QStandardItem, QStandardItemModel

from .api.country_urls_fetcher import CountryUrlsFetcher
from .constants import RADIOBUTTONS_SERVICES
from .utils import QtCompat

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'integrator_uslug_danych_przestrzennych_dialog_base.ui'))


class IntegratorUslugPrzestrzennychDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(IntegratorUslugPrzestrzennychDialog, self).__init__(parent)
        self.setupUi(self)
        self.qt_compat = QtCompat()
        self.country_urls_fetcher = CountryUrlsFetcher()
        self.country_services_cache: List[Dict[str, str]] = []
        self.setupDialog()
        self.setupSignals()
        self.setupTable()

    def setupDialog(self) -> None:
        self.img_main.setMargin(9)

    def setupSignals(self) -> None:
        for obj in RADIOBUTTONS_SERVICES:
            widget_obj = getattr(self, obj)
            widget_obj.toggled.connect(self.setupTable)
        self.search_lineedit.textChanged.connect(self.applySearchFilter)

    def setupTable(self) -> None:
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Nazwa uslugi', 'Adres uslugi'])
        self.fillServicesTable()
        self.configureTableHeader()
        self.setupSearch()
        self.applySearchFilter(self.search_lineedit.text())

    def configureTableHeader(self) -> None:
        resize_interactive = self.qt_compat.getEnum(QtWidgets.QHeaderView, 'ResizeMode', 'Interactive')
        header = self.services_table.horizontalHeader()
        header.setSectionResizeMode(0, resize_interactive)
        self.services_table.setColumnWidth(0, 400)
        header.setSectionResizeMode(1, resize_interactive)
        self.services_table.setColumnWidth(1, 500)
        ascending = self.qt_compat.getEnum(Qt, 'SortOrder', 'AscendingOrder')
        self.services_table.horizontalHeader().setSortIndicator(0, ascending)
        self.services_table.setSortingEnabled(True)
        header = self.services_table.verticalHeader()
        align_center = self.qt_compat.getEnum(Qt, 'AlignmentFlag', 'AlignCenter')
        header.setDefaultAlignment(align_center)

    def fillServicesTable(self) -> None:
        for service_row in self.getServicesRows():
            row = [
                QStandardItem(service_row['dataset_name']),
                QStandardItem(service_row['url']),
            ]
            self.model.appendRow(row)
        self.services_table.setModel(self.model)

    def setupSearch(self) -> None:
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterKeyColumn(0)
        self.services_table.setModel(self.proxy_model)

    def applySearchFilter(self, text: str) -> None:
        case_insensitive = self.qt_compat.getEnum(Qt, 'CaseSensitivity', 'CaseInsensitive')
        self.proxy_model.setFilterCaseSensitivity(case_insensitive)
        self.proxy_model.setFilterFixedString(text)

    def getServicesRows(self) -> List[Dict[str, str]]:
        service_type = 'WMS' if self.wms_rdbtn.isChecked() else 'WFS'
        return self.country_urls_fetcher.getCountryUrlsByServiceType(self.country_services_cache, service_type)

    def getSelectedServicesUrls(self) -> Dict[str, str]:
        model = self.services_table.model()
        selected_indexes = self.services_table.selectionModel().selectedRows()
        values = {}
        for index in selected_indexes:
            name_index = model.index(index.row(), 0)
            value_index = model.index(index.row(), 1)
            values[model.data(name_index)] = model.data(value_index)
        return values

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.country_services_cache = self.country_urls_fetcher.fetchCountryUrls()
        self.setupTable()
        self.wms_rdbtn.setFocus()

    def closeEvent(self, event: QShowEvent) -> None:
        event.accept()
        self.accept()
