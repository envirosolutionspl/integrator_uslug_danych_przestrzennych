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
from typing import Dict, List, Callable

from qgis.PyQt.QtWidgets import QProgressDialog
from qgis.PyQt.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QEventLoop

from .. import PLUGIN_NAME as plugin_name
from ..modules.country_urls_fetcher import CountryUrlsFetcher
from ..modules.standalone_urls_fetcher import StandaloneUrlsFetcher
from ..modules.add_service import AddOGCService
from ..utils import QtCompat, SingleTaskManager, MessageUtils, NetworkManager

class ContentManager(QObject):
    data_updated_signal = pyqtSignal(int) 

    def __init__(self, dialog_parent):
        super().__init__()
        self.dialog_parent = dialog_parent
        self.network_manager = NetworkManager()
        self.ogc_service = AddOGCService(self.network_manager)
        self.data_updated_signal.connect(self._noSignalConnected)
        
        # Sekcja API
        self.country_urls_fetcher = CountryUrlsFetcher()
        self.country_services_cache: List[Dict[str, str]] = []

        # Sekcja STANDALONE
        self.standalone = StandaloneUrlsFetcher()
        self.use_standalone_data = False
        self.standalone_services_cache: List[Dict[str, str]] = []
        self.standalone_fetch_task = SingleTaskManager(self._fetchStanaloneServices, self._finishStanaloneServicesFetch, 'Pobieranie usług z alternatywnego źródła')
        self.is_standalone_services_cache_ready = False
        self.refresh_table_function = None

    def _fetchStanaloneServices(self):
        self.standalone_services_cache = self.standalone.fetch() 

    def _finishStanaloneServicesFetch(self):
        self.is_standalone_services_cache_ready = True
        if self.use_standalone_data:
            self.country_services_cache = self.standalone_services_cache
            self.data_updated_signal.emit(len(self.country_services_cache))
            
    @pyqtSlot(int)
    def _noSignalConnected(self, ilosc_pobrana: int):
        MessageUtils.logInfo(
                f"Pobrano dane o usługach ze stron www.geoportal.gov.pl oraz integracja.gugik.gov.pl. "
                f"Ilość dostępnych usług na dzień dzisiejszy to: {ilosc_pobrana}"
            )
        if self.refresh_table_function is not None and callable(self.refresh_table_function):
            self.refresh_table_function()

    def setTableRefreshFunction(self, func: Callable = None):
        self.refresh_table_function = func

    def isStandaloneFetchTaskRunning(self):
        return self.standalone_fetch_task.isRunning()

    def isStandaloneServicesCacheReady(self):
        return self.is_standalone_services_cache_ready
    
    def getCountryServicesCache(self):
        return self.country_services_cache
    
    def getCountryUrlsByServiceType(self, service_type: str) -> List[Dict[str, str]]:
        normalized_type = service_type.strip().upper()
        return [row for row in self.country_services_cache if row.get('service_type') == normalized_type]

    def servicesCacheInit(self):
        " Pobieranie danych z sieci podczas pierwszego uruchomienia "
        # Próba pobrania danych z serwera API
        if not self.use_standalone_data and len(self.country_services_cache) == 0:
            self.country_services_cache = self.country_urls_fetcher.fetchCountryUrls()
        if len(self.country_services_cache) > 0:
            MessageUtils.logInfo(
                f"Pobrano dane o usługach z zewnętrznego API. "
                f"Ilość dostępnych usług na dzień dzisiejszy to: {len(self.country_services_cache)}"
            )
            return

        # Próba scrapowania danych w przypadku niedostępności API
        if not self.use_standalone_data:
            MessageUtils.pushMessageBoxWarning(
                self.dialog_parent, "Komunikat",
                "Nie można pobrać usług z serwera.\nSpróbuj ponownie."
            )
            self.use_standalone_data = True
            self.standalone_fetch_task.run()

    def addServiceFromSelection(self, table_proxy_model, selected_table_indexes, selected_service_type: str):
        " Dodaje usługi do mapy według podanych: tabeli i zaznaczenia "
        selected_services = {}
        for index in selected_table_indexes:
            name_index = table_proxy_model.index(index.row(), 0)
            value_index = table_proxy_model.index(index.row(), 1)
            selected_services[table_proxy_model.data(name_index)] = table_proxy_model.data(value_index)

        if not selected_services:
            MessageUtils.pushMessageBoxWarning(
                self.dialog_parent,
                'Ostrzeżenie',
                'Nie wybrano żadnej usługi z listy.'
            )
            return

        progress = QProgressDialog("Pobieranie i dodawanie usług. Proces może potrwać kilka minut..", "Anuluj", 0, len(selected_table_indexes)+1, self.dialog_parent)
        progress.setWindowTitle(plugin_name)
        progress.setWindowModality(QtCompat.getEnum(Qt, 'WindowModality', 'WindowModal'))
        progress.setAutoClose(True)
        progress.setAutoReset(True)
        progress.setMinimumDuration(0)   # natychmiast pokaż
        progress.setCancelButtonText("Anuluj")
        progress.show()
        loop = QEventLoop(self.dialog_parent)
        for name, url in selected_services.items():
            self.ogc_service.downloadServices(name, url, selected_service_type)
            if progress.value() < progress.maximum():
                progress.setValue(progress.value()+1)
                loop.processEvents()
            if progress.wasCanceled():
                self.ogc_service.clearCache()       
                break
        
        successfully_add = self.ogc_service.addServices()
        progress.setValue(progress.maximum())

        if successfully_add:
            MessageUtils.pushMessageBoxInfo(self.dialog_parent, 'Informacja', '\n'.join(
                f'Dodano usługe {key}' if value else f'Nie dodano usługi {key}'
                for key, value in successfully_add.items()
            ))
        else:
            MessageUtils.pushMessageBoxInfo(self.dialog_parent, 'Informacja', 'Nie dodano żadnych usług')

        progress.deleteLater()
        progress = None