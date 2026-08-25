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
from qgis.PyQt.QtGui import QStandardItem, QStandardItemModel
from .utils import QtCompat

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'integrator_uslug_danych_przestrzennych_dialog_which_layers.ui'))

class ChooseLayersDialog(QtWidgets.QDialog, FORM_CLASS):

    def __init__(self,
                 service_name: str,
                 service_url: str,
                 available_layers: list[dict],
                 parent=None,
    ):
        super().__init__(parent)
        self.setupUi(self)
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels([
            'Nazwa warstwy',
            'Identyfikator',
        ])
        self.services_table.setModel(self.model)

        # Proxy do filtrowania warstw w search barze
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterKeyColumn(0)

        self.services_table.setModel(self.proxy_model)
        self.services_table.setSelectionBehavior(
            QtCompat.getEnum(
                QTableView,
                'SelectionBehavior',
                'SelectRows',
                )
            )
        self.services_table.setSelectionMode(
            QtCompat.getEnum(
                QTableView,
                'SelectionMode',
                'MultiSelection',
                )
            )

        self.search_lineedit.textChanged.connect(self.applySearchFilter)

        self.service_name = service_name
        self.link_do_uslugi.setText(service_url)
        self.available_layers = available_layers

        self.addLayersToTable()
        self.add_btn.clicked.connect(self.accept)

    def addLayersToTable(self) -> None:
        for layer in self.available_layers:
            title_item = QStandardItem(layer['title'])
            id_item = QStandardItem(layer['id'])

            title_item.setEditable(False)
            id_item.setEditable(False)

            self.model.appendRow([
                title_item,
                id_item,
            ])

    def getSelectedLayerIds(self) -> list:
        selected_rows = self.services_table.selectionModel().selectedRows(1)
        selected_ids = [index.data() for index in selected_rows]

        return selected_ids
    
    def applySearchFilter(self, text) -> None:
        case_insensitive = QtCompat.getEnum(Qt, 'CaseSensitivity', 'CaseInsensitive')

        self.proxy_model.setFilterCaseSensitivity(case_insensitive)
        self.proxy_model.setFilterFixedString(text)

