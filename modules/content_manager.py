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
from typing import Dict, List

from qgis.PyQt.QtWidgets import QProgressDialog
from qgis.PyQt.QtCore import Qt, QObject, QEventLoop

from .. import PLUGIN_NAME as plugin_name
from ..modules.country_urls_fetcher import CountryUrlsFetcher
from ..modules.add_service import AddOGCService
from ..utils import QtCompat, MessageUtils
from ..constants import SERVICE_TYPES

class ContentManager(QObject):

    def __init__(self, dialog_parent):
        super().__init__()
        self.dialog_parent = dialog_parent
        self.ogc_service = AddOGCService()
        
        # Sekcja API
        self.country_urls_fetcher = CountryUrlsFetcher()
        self.country_services_cache: List[Dict[str, str]] = []
    
    def getCountryServicesCache(self):
        """Zwraca listę z usługami na poziomie krajowym"""
        return self.country_services_cache
    
    def getCountryUrlsByServiceType(self, service_type: str) -> List[Dict[str, str]]:
        """Zwraca listę z usługami na poziomie krajowym, według wybranego typu usługi"""
        normalized_type = service_type.strip().upper()
        return [row for row in self.country_services_cache if row.get('service_type') == normalized_type]

    def servicesCacheInit(self) -> bool:
        """Pobieranie danych krajowych z API. Pobiera tylko gdy cache jest pusty. Zwraca False, gdy cache jest dalej pusty."""
        # Próba pobrania danych z serwera API
        if len(self.country_services_cache) == 0:
            self.country_services_cache = []
            for service_type in SERVICE_TYPES:
                self.country_services_cache.extend(self.country_urls_fetcher.fetchCountryUrls('PL', service_type.upper()))
            if len(self.country_services_cache) > 0:
                MessageUtils.logInfo(
                    f"Pobrano dane o usługach z zewnętrznego API. "
                    f"Ilość dostępnych usług na dzień dzisiejszy to: {len(self.country_services_cache)}"
                )
                return True
            return False
        return True
    
    def addServiceFromSelection(self, table_proxy_model, selected_table_indexes, selected_service_type: str):
        """Dodaje usługi do mapy według podanych: tabeli i zaznaczenia"""
        # Pobranie wyboru usług z tabeli
        selected_services = {}
        for index in selected_table_indexes:
            name_index = table_proxy_model.index(index.row(), 0)
            value_index = table_proxy_model.index(index.row(), 1)
            selected_services[table_proxy_model.data(value_index)] = table_proxy_model.data(name_index)

        if not selected_services:
            MessageUtils.pushMessageBoxWarning(
                self.dialog_parent,
                'Ostrzeżenie',
                'Nie wybrano żadnej usługi z listy.'
            )
            return

        # Utworzenie okna progresu
        progress = QProgressDialog("Pobieranie i dodawanie usług. Proces może potrwać kilka minut..", "Anuluj", 0, len(selected_table_indexes)+1, self.dialog_parent)
        self._appendDefaultProgressDialogSettings(progress)
        progress.show()

        # Utworzenie szkieletu warstw w pamięci
        loop = QEventLoop(self.dialog_parent)
        for url, name in selected_services.items():
            self.ogc_service.downloadServices(name, url, selected_service_type)
            if progress.value() < progress.maximum():
                progress.setValue(progress.value()+1)
                loop.processEvents()
            if progress.wasCanceled():
                self.ogc_service.clearCache()       
                break
        
        # Finalizowanie dodawania usług poprzez dodanie ich do projektu QGIS
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

    def _appendDefaultProgressDialogSettings(self, progress_dialog):
        """Przypisuje postawowe zachowanie okna progresu"""

        def _cancelProgressDialog():
            """Obsługuje przycik Anuluj"""
            self.ogc_service.cancelTasks() # wysyła sygnał do klasy dodającej usługę
            progress_dialog.setLabelText("Przerywanie operacji. Proszę czekać...")
            progress_dialog.show() # zapobiega chowaniu się okna

        progress_dialog.canceled.connect(_cancelProgressDialog)

        progress_dialog.setWindowTitle(plugin_name)
        progress_dialog.setWindowModality(QtCompat.getEnum(Qt, 'WindowModality', 'WindowModal'))
        progress_dialog.setAutoClose(False)
        progress_dialog.setAutoReset(False)
        progress_dialog.setMinimumDuration(0)   # natychmiast pokaż
        progress_dialog.setCancelButtonText("Anuluj")