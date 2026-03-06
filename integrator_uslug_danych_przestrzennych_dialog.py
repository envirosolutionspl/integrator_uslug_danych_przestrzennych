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
        self.qtCompat = QtCompat()
        self.countryUrlsFetcher = CountryUrlsFetcher()
        self.countryServicesCache: List[Dict[str, str]] = []
        self.setupDialog()
        self.setupSignals()
        self.setupTable()

    def setupDialog(self) -> None:
        self.img_main.setMargin(9)

    def setupSignals(self) -> None:
        for obj in RADIOBUTTONS_SERVICES:
            widgetObj = getattr(self, obj)
            widgetObj.toggled.connect(self.setupTable)
        self.search_lineedit.textChanged.connect(self.applySearchFilter)

    def setupTable(self) -> None:
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Nazwa uslugi', 'Adres uslugi'])
        self.fillServicesTable()
        self.configureTableHeader()
        self.setupSearch()
        self.applySearchFilter(self.search_lineedit.text())

    def configureTableHeader(self) -> None:
        resizeInteractive = self.qtCompat.getEnum(QtWidgets.QHeaderView, 'ResizeMode', 'Interactive')
        header = self.services_table.horizontalHeader()
        header.setSectionResizeMode(0, resizeInteractive)
        self.services_table.setColumnWidth(0, 400)
        header.setSectionResizeMode(1, resizeInteractive)
        self.services_table.setColumnWidth(1, 500)
        ascending = self.qtCompat.getEnum(Qt, 'SortOrder', 'AscendingOrder')
        self.services_table.horizontalHeader().setSortIndicator(0, ascending)
        self.services_table.setSortingEnabled(True)
        header = self.services_table.verticalHeader()
        alignCenter = self.qtCompat.getEnum(Qt, 'AlignmentFlag', 'AlignCenter')
        header.setDefaultAlignment(alignCenter)

    def fillServicesTable(self) -> None:
        for serviceRow in self.getServicesRows():
            row = [
                QStandardItem(serviceRow['datasetName']),
                QStandardItem(serviceRow['url']),
            ]
            self.model.appendRow(row)
        self.services_table.setModel(self.model)

    def setupSearch(self) -> None:
        self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setSourceModel(self.model)
        self.proxyModel.setFilterKeyColumn(0)
        self.services_table.setModel(self.proxyModel)

    def applySearchFilter(self, text: str) -> None:
        caseInsensitive = self.qtCompat.getEnum(Qt, 'CaseSensitivity', 'CaseInsensitive')
        self.proxyModel.setFilterCaseSensitivity(caseInsensitive)
        self.proxyModel.setFilterFixedString(text)

    def getServicesRows(self) -> List[Dict[str, str]]:
        serviceType = 'WMS' if self.wms_rdbtn.isChecked() else 'WFS'
        return self.countryUrlsFetcher.getCountryUrlsByServiceType(self.countryServicesCache, serviceType)

    def getSelectedServicesUrls(self) -> Dict[str, str]:
        model = self.services_table.model()
        selectedIndexes = self.services_table.selectionModel().selectedRows()
        values = {}
        for index in selectedIndexes:
            nameIndex = model.index(index.row(), 0)
            valueIndex = model.index(index.row(), 1)
            values[model.data(nameIndex)] = model.data(valueIndex)
        return values

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.countryServicesCache = self.countryUrlsFetcher.fetchCountryUrls()
        self.setupTable()
        self.wms_rdbtn.setFocus()

    def closeEvent(self, event: QShowEvent) -> None:
        event.accept()
        self.accept()
