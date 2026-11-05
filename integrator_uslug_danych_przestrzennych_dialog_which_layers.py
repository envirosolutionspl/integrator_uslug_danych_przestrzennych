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

from qgis.PyQt import QtWidgets
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QTableView
from qgis.PyQt.QtCore import QDir, QEvent, QSortFilterProxyModel, Qt
from qgis.PyQt.QtGui import QStandardItem, QStandardItemModel
from .utils import QtCompat, ThemeUtils

PLUGIN_DIR = os.path.dirname(__file__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Prefiks "iudpimg:" używany w url(...) arkusza stylów w pliku .ui.
# Musi być zarejestrowany PRZED setupUi, inaczej QSS nie znajdzie ikon.
QDir.addSearchPath('iudpimg', os.path.join(PLUGIN_DIR, 'images'))

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    PLUGIN_DIR, 'ui', 'integrator_uslug_danych_przestrzennych_dialog_which_layers.ui'))


class ChooseLayersDialog(QtWidgets.QDialog, FORM_CLASS):

    def __init__(self,
                 service_name: str,
                 available_layers: list[dict],
                 parent=None,
                 ):
        super().__init__(parent)
        self.setupUi(self)
        self._theme = None
        self._applyTheme()
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
        self.layers_table.selectionModel().selectionChanged.connect(self.updateSelectedCount)
        self.addLayersToTable()
        self.add_btn.clicked.connect(self.accept)
        self.updateSelectedCount()

    def updateSelectedCount(self, *args) -> None:
        """Wpisuje liczbę zaznaczonych warstw; bez zaznaczenia "Dodaj zaznaczone" jest nieaktywny"""
        count = len(self.layers_table.selectionModel().selectedRows())
        self.lbl_selected_count.setText('Zaznaczono: %d %s' % (count, self._layersWord(count)))
        self.add_btn.setEnabled(count > 0)

    @staticmethod
    def _layersWord(count: int) -> str:
        """Odmiana słowa "warstwa" przez liczbę"""
        if count == 1:
            return 'warstwa'
        if count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
            return 'warstwy'
        return 'warstw'

    def _applyTheme(self, force=False) -> None:
        """Ustawia właściwość "theme" - kolory zdefiniowane w arkuszu stylów w pliku .ui."""
        theme = 'dark' if ThemeUtils.isDarkTheme() else 'light'
        if theme == self._theme and not force:
            return
        self._theme = theme
        self.setProperty('theme', theme)
        ThemeUtils.repolishAll(self)

    def showEvent(self, event) -> None:
        self._applyTheme()
        super().showEvent(event)

    def changeEvent(self, event) -> None:
        # changeEvent przychodzi już w trakcie setupUi - wtedy _theme jeszcze nie istnieje
        if (event.type() in (QEvent.Type.PaletteChange, QEvent.Type.StyleChange)
                and getattr(self, '_theme', None) is not None):
            self._applyTheme()
        super().changeEvent(event)

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
