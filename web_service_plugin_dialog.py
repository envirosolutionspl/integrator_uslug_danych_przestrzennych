# -*- coding: utf-8 -*-
import os
import sys
from functools import partial

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import Qt, QSortFilterProxyModel
from qgis.PyQt.QtWidgets import QComboBox, QWidget
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem, QShowEvent
from typing import Any, Dict, Tuple, List

from .api.eziudp_services_fetcher import EziudpServicesFetcher
from .api.geoportal_services_fetcher import GeoportalServicesFetcher
from .constants import (
    ADMINISTRATIVE_UNITS_OBJECTS,
    CHECKBOXES,
    RADIOBUTTONS,
    CHECKBOX_COMBOBOX_LINK,
    CHECKBOX_TYPES_LINK,
    COMBOBOX_CHECKBOX_LINK
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'web_service_plugin_dialog_base.ui'))


class WebServicePluginDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, regionFetch, parent=None):
        super(WebServicePluginDialog, self).__init__(parent)
        self.setupUi(self)
        self.geoportal_fetcher = GeoportalServicesFetcher()
        self.eziudp_fetcher = EziudpServicesFetcher()
        self.regionFetch = regionFetch
        self._setup_dialog()
        self._setup_signals()
        self.setup_table()
        self.setup_search()

    def _setup_dialog(self) -> None:
        self.fill_voivodeships()

    def _setup_signals(self) -> None:
        self.kraj_check.clicked.connect(partial(self.wojewodztwo_combo.setCurrentIndex, -1))
        for base_combo, combo_items in ADMINISTRATIVE_UNITS_OBJECTS.items():
            fetch_func, dependent_combo = combo_items
            combo_obj = getattr(self, base_combo)
            combo_obj.currentTextChanged.connect(
                partial(self.setup_administrative_unit_obj, fetch_func, dependent_combo)
            )
        widgets = [*CHECKBOXES, *RADIOBUTTONS]
        for obj in widgets:
            widget_obj = getattr(self, obj)
            widget_obj.toggled.connect(self.setup_table)
        for combo_name in CHECKBOX_COMBOBOX_LINK.keys():
            combo_obj = getattr(self, combo_name)
            combo_obj.currentTextChanged.connect(self.reload_table_by_teryt)
        for obj in CHECKBOXES:
            checkbox_obj = getattr(self, obj)
            checkbox_obj.stateChanged.connect(self.enable_comboboxes)
        self.search_lineedit.textChanged.connect(self.apply_search_filter)

    def setup_table(self) -> None:
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Nazwa usługi', 'Adres usługi'])
        self.fill_services_table()
        self.configure_table_header()
        self.setup_search()

    def configure_table_header(self) -> None:
        header = self.services_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        self.services_table.setColumnWidth(0, 400)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
        self.services_table.setColumnWidth(1, 500)
        self.services_table.horizontalHeader().setSortIndicator(0, Qt.AscendingOrder)
        self.services_table.setSortingEnabled(True)
        header = self.services_table.verticalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)

    def fill_services_table(self) -> None:
        dataset_dict = self.get_services_dict()
        for service_name, service_url in dataset_dict.items():
            urls = service_url if isinstance(service_url, list) else [service_url]
            for url in urls:
                row = [
                    QStandardItem(service_name),
                    QStandardItem(url),
                ]
                self.model.appendRow(row)
        self.services_table.setModel(self.model)

    def reload_table_by_teryt(self) -> None:
        sender_name = self.sender().objectName()
        if getattr(self, CHECKBOX_COMBOBOX_LINK.get(sender_name)).isChecked():
            self.setup_table()

    def fill_voivodeships(self) -> None:
        voivodeships_ids = self.regionFetch.wojewodztwo_dict.keys()
        voivodeships_names = self.regionFetch.wojewodztwo_dict.values()
        self.wojewodztwo_combo.clear()
        self.wojewodztwo_combo.addItems(voivodeships_names)
        for idx, val in enumerate(voivodeships_ids):
            self.wojewodztwo_combo.setItemData(idx, val)
        self.wojewodztwo_combo.setCurrentIndex(-1)

    def setup_administrative_unit_obj(self, func: Any, dependent_combo: str) -> None:
        combo_obj = getattr(self, dependent_combo)
        unit_data = self.sender().currentData()
        combo_obj.clear()
        combo_obj.blockSignals(True)
        if unit_data:
            unit_dict = getattr(self.regionFetch, func)(unit_data)
            combo_obj.addItems(unit_dict.values())
            for idx, val in enumerate(unit_dict.keys()):
                combo_obj.setItemData(idx, val)
        combo_obj.setCurrentIndex(-1)
        combo_obj.blockSignals(False)

    def setup_comboboxes(self, widget: QWidget) -> None:
        for child in widget.children():
            if isinstance(child, QComboBox):
                child.setCurrentIndex(-1)
            elif isinstance(child, QWidget):
                self.setup_comboboxes(child)

    def setup_search(self) -> None:
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterKeyColumn(0)
        self.services_table.setModel(self.proxy_model)

    def apply_search_filter(self, text: str) -> None:
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterFixedString(text)

    def enable_comboboxes(self) -> None:
        comboboxes_to_hide = []
        if self.sender().objectName() == 'kraj_check':
            comboboxes_to_hide = list(COMBOBOX_CHECKBOX_LINK.values())
        else:
            for check, cmb in COMBOBOX_CHECKBOX_LINK.items():
                combo_obj = getattr(self, cmb)
                combo_obj.setEnabled(True)
                if getattr(self, check).isChecked():
                    combo_idx = list(COMBOBOX_CHECKBOX_LINK).index(check) + 1
                    comboboxes_to_hide = list(list(COMBOBOX_CHECKBOX_LINK.values())[combo_idx:])
                    break
        for combo in comboboxes_to_hide:
            combo_obj = getattr(self, combo)
            combo_obj.setEnabled(False)

    def get_services_dict(self) -> Dict[str, str]:
        if self.kraj_check.isChecked():
            return self.get_servives_dict_for_pl()
        else:
            return self.get_servives_dict_by_teryt()

    def get_servives_dict_for_pl(self) -> Dict[str, str]:
        if self.wms_rdbtn.isChecked():
            services = {
                **self.geoportal_fetcher.get_wms_wmts_services(),
                **self.eziudp_fetcher.get_servives_wms_wmts_dict_for_pl()
            }
        else:
            services = {
                **self.geoportal_fetcher.get_wfs_wcs_services(),
                **self.eziudp_fetcher.get_servives_wfs_wcs_dict_for_pl()
            }
        return services

    def get_current_type_and_teryt(self) -> Tuple[str, str]:
        for combo_name, checkbox_name in CHECKBOX_COMBOBOX_LINK.items():
            check_obj = getattr(self, checkbox_name)
            if check_obj.isChecked():
                return CHECKBOX_TYPES_LINK.get(checkbox_name), getattr(self, combo_name).currentData()

    def get_servives_dict_by_teryt(self) -> Dict[str, str]:
        unit_type, teryt = self.get_current_type_and_teryt()
        if self.wms_rdbtn.isChecked():
            services = self.eziudp_fetcher.get_services_wms_wmts_by_teryt(unit_type, teryt)
        else:
            services = self.eziudp_fetcher.get_services_wfc_wcs_by_teryt(unit_type, teryt)
        return services

    def get_selected_services_urls(self) -> Dict[str, str]:
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
        self.wms_rdbtn.setFocus()

    def closeEvent(self, event: QShowEvent) -> None:
        self.setup_comboboxes(self)
        event.accept()
        self.accept()

