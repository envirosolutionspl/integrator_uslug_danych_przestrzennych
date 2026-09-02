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
                 available_layers: list[dict],
                 parent=None,
    ):
        super().__init__(parent)
        self.setupUi(self)
        self.qt_compat = QtCompat()
        self.model = QStandardItemModel()
        self.available_layers = available_layers

        self.user_role = self.qt_compat.getEnum(Qt, 'ItemDataRole', 'UserRole')

        self.search_lineedit.textChanged.connect(self.applySearchFilter)
        self.zaznacz_wszystkie_warstwy.clicked.connect(self.selectAllLayers)
        self.service_name = service_name
        self.link_do_uslugi.setText(self.service_name)

        self.confiureServicesTable()
        self.layers_table.selectionModel().selectionChanged.connect(self.updateSelectAllCheckbox)
        self.addLayersToTable()
        self.add_btn.clicked.connect(self.accept)

    def addLayersToTable(self) -> None:
        for layer in self.available_layers:
            title_item = QStandardItem(layer['title'])

            title_item.setEditable(False)

            title_item.setData(
                layer['id'],
                self.user_role,
            )

            self.model.appendRow([
                title_item,
            ])

    def getSelectedLayerIds(self) -> list:
        selected_rows = self.layers_table.selectionModel().selectedRows(0)
        selected_ids = [index.data(self.user_role) for index in selected_rows]

        return selected_ids
    
    def applySearchFilter(self, text) -> None:
        case_insensitive = self.qt_compat.getEnum(Qt, 'CaseSensitivity', 'CaseInsensitive')

        self.proxy_model.setFilterCaseSensitivity(case_insensitive)
        self.proxy_model.setFilterFixedString(text)

        self.updateSelectAllCheckbox()

    def confiureServicesTable(self) -> None:
        self.model.setHorizontalHeaderLabels([
            'Nazwa warstwy',
        ])

        # Proxy do filtrowania warstw w search barze
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterKeyColumn(0)
        self.layers_table.setModel(self.proxy_model)


        h_header = self.layers_table.horizontalHeader()
        resize_stretch = self.qt_compat.getEnum(
            QtWidgets.QHeaderView,
            'ResizeMode',
            'Stretch',
        )

        align_center = self.qt_compat.getEnum(
            Qt,
            'AlignmentFlag',
            'AlignCenter',
        )
        h_header.setSectionResizeMode(0, resize_stretch)
        h_header.setDefaultAlignment(align_center)

        self.layers_table.setSelectionBehavior(
            self.qt_compat.getEnum(
                QTableView,
                'SelectionBehavior',
                'SelectRows',
                )
            )
        self.layers_table.setSelectionMode(
            self.qt_compat.getEnum(
                QTableView,
                'SelectionMode',
                'MultiSelection',
                )
            )

    def selectAllLayers(self, checked: bool) -> None:
        if checked:
            self.layers_table.selectAll()
        else:
            self.layers_table.clearSelection()

    def updateSelectAllCheckbox(self) -> None:
        selected = len(self.layers_table.selectionModel().selectedRows())
        total = self.proxy_model.rowCount()
        self.zaznacz_wszystkie_warstwy.setChecked(total > 0 and selected == total)