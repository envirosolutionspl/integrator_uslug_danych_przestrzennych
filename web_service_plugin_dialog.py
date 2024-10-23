# -*- coding: utf-8 -*-
import os
import sys

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWidgets import QComboBox, QWidget
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem, QShowEvent
from typing import Any, Dict, Tuple

from .api.eziudp_services_fetcher import EziudpServicesFetcher
from .api.geoportal_services_fetcher import GeoportalServicesFetcher
from .constants import (
    ADMINISTRATIVE_UNITS_OBJECTS,
    CHECKBOXES,
    RADIOBUTTONS,
    CHECKBOX_COMBOBOX_LINK, CHECKBOX_TYPES_LINK
)
from .api.region_fetch import RegionFetch

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'web_service_plugin_dialog_base.ui'))


class WebServicePluginDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(WebServicePluginDialog, self).__init__(parent)
        self.setupUi(self)
        self.geoportal_fetcher = GeoportalServicesFetcher()
        self.eziudp_fetcher = EziudpServicesFetcher()
        self._setup_dialog()
        self._setup_signals()
        self.setup_table()

    def _setup_dialog(self) -> None:
        self.regionFetch = RegionFetch(teryt='')
        self.fill_voivodeships()

    def _setup_signals(self) -> None:
        for base_combo, combo_items in ADMINISTRATIVE_UNITS_OBJECTS.items():
            fetch_func, dependent_combo = combo_items
            combo_obj = getattr(self, base_combo)
            combo_obj.currentTextChanged.connect(
                lambda _, func=fetch_func, combo=dependent_combo: self.setup_administrative_unit_obj(func, combo)
            )
        for obj in [*CHECKBOXES, *RADIOBUTTONS]:
            getattr(self, obj).toggled.connect(self.setup_table)
        for combo_name in CHECKBOX_COMBOBOX_LINK.keys():
            getattr(self, combo_name).currentTextChanged.connect(self.reload_table_by_teryt)

    def setup_table(self) -> None:
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Nazwa usługi', 'Adres usługi'])
        self.fill_services_table()
        header = self.services_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        self.services_table.setColumnWidth(0, 400)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
        self.services_table.setColumnWidth(1, 500)

    def fill_services_table(self) -> None:
        dataset_dict = self.get_services_dict()
        for service_name, service_url in dataset_dict.items():
            row = [
                QStandardItem(service_name),
                QStandardItem(service_url),
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

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.wms_rdbtn.setFocus()

    def closeEvent(self, event: QShowEvent) -> None:
        self.setup_comboboxes(self)
        event.accept()
        self.accept()

