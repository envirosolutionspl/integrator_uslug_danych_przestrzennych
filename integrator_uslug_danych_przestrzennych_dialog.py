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
import configparser
import os
import re
import sys
from typing import Dict, List

from qgis.PyQt import QtWidgets
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QTableView
from qgis.PyQt.QtCore import QDir, QEvent, QSortFilterProxyModel, Qt, QTimer, QUrl
from qgis.PyQt.QtGui import QDesktopServices, QShowEvent, QStandardItem, QStandardItemModel
from .modules.content_manager import ContentManager
from .constants import (
    ADD_SERVICE_CONNECTIONS_CHECK,
    FOOTER_LINK_COLORS,
    FOOTER_LOGOS,
    HOME_LINK,
    MSG_SERVICES_UNAVAILABLE,
    RADIOBUTTONS_SERVICES,
    TABLE_CONNECTIONS_CHECK,
)
from .utils import QtCompat, SingleTaskManager, MessageUtils, ServiceAPI, ThemeUtils

PLUGIN_DIR = os.path.dirname(__file__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Prefiks "iudpimg:" używany w url(...) arkusza stylów w pliku .ui.
# Musi być zarejestrowany PRZED setupUi, inaczej QSS nie znajdzie ikon.
QDir.addSearchPath('iudpimg', os.path.join(PLUGIN_DIR, 'images'))

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    PLUGIN_DIR, 'ui', 'integrator_uslug_danych_przestrzennych_dialog_base.ui'))


class IntegratorUslugPrzestrzennychDialog(QtWidgets.QDockWidget, FORM_CLASS):

    is_window_shown = False

    def __init__(self, parent=None):
        super(IntegratorUslugPrzestrzennychDialog, self).__init__(parent)
        self.setupUi(self)
        self._theme = None
        self._applyTheme()
        self._setupLook()
        self.qt_compat = QtCompat()

        self.content_manager = ContentManager(self)
        self.serv_rows = []
        self.table_setup_task = SingleTaskManager(self._fetchServices, self._finishTableSetup)
        self.plugin_name = ''
        # True, gdy tabela pokazuje komunikat (pushMessageOverTable) zamiast listy usług
        self._is_message_shown = False

        self.setupSignals()

        # Inicjacja tabeli
        self.model = QStandardItemModel()
        self.configureTableHeader()
        self.setupSearch()
        self.setupSelectedCount()
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

        h_header = self.services_table.horizontalHeader()
        h_header.setSectionResizeMode(0, resize_stretch)
        h_header.setSectionResizeMode(1, resize_stretch)
        h_header.setDefaultAlignment(align_center)

        # Ustawienia pionowe
        v_header = self.services_table.verticalHeader()
        v_header.setDefaultSectionSize(24)
        v_header.setDefaultAlignment(align_center)

        self.services_table.setSortingEnabled(True)
        self.services_table.setSelectionBehavior(self.qt_compat.getEnum(QTableView, 'SelectionBehavior', 'SelectRows'))
        self.services_table.setSelectionMode(self.qt_compat.getEnum(QTableView, 'SelectionMode', 'MultiSelection'))

    def setupSearch(self) -> None:
        """Konfiguracja modelu proxy dla pola wyszukiwania"""
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterKeyColumn(0)
        self.services_table.setModel(self.proxy_model)

    def setupSelectedCount(self) -> None:
        """Liczniki usług (w tabeli i zaznaczonych) oraz dostępność "Dodaj zaznaczone"
        - aktualizowane przy zmianie zaznaczenia i zawartości tabeli"""
        self.services_table.selectionModel().selectionChanged.connect(self.updateSelectedCount)
        self.proxy_model.rowsInserted.connect(self.updateSelectedCount)
        self.proxy_model.rowsRemoved.connect(self.updateSelectedCount)
        self.proxy_model.modelReset.connect(self.updateSelectedCount)
        self.proxy_model.layoutChanged.connect(self.updateSelectedCount)
        self.updateSelectedCount()

    def updateSelectedCount(self, *args) -> None:
        """Wpisuje liczbę usług w tabeli i zaznaczonych; bez zaznaczenia "Dodaj zaznaczone" jest nieaktywny"""
        # w trybie komunikatu (pushMessageOverTable) jedyny wiersz tabeli nie jest usługą
        is_message = self._is_message_shown
        total = 0 if is_message else self.proxy_model.rowCount()
        count = 0 if is_message else len(self.services_table.selectionModel().selectedRows())
        self.lbl_services_count.setText('%d %s' % (total, self._servicesWord(total)))
        self.lbl_selected_count.setText('Zaznaczono: %d %s' % (count, self._servicesWord(count)))
        self.add_btn.setEnabled(count > 0)

    @staticmethod
    def _servicesWord(count: int) -> str:
        """Odmiana słowa "usługa" przez liczbę"""
        if count == 1:
            return 'usługa'
        if count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
            return 'usługi'
        return 'usług'

    def setupDialog(self, plugin_name, plugin_version) -> None:
        """Ustawienie podstawowych danych okna dialogowego"""
        self.lbl_pluginVersion.setText('v%s' % plugin_version)
        self.plugin_name = plugin_name

    # =============================
    # Wygląd

    def _setupLook(self) -> None:
        """Elementy wyglądu, których nie da się opisać w pliku .ui."""
        self.btn_help.clicked.connect(self._openHelp)
        self.btn_close.clicked.connect(self.close)
        self._setupTitleBar()

    def _setupTitleBar(self) -> None:
        """Nagłówek wtyczki jako pasek tytułu panelu - zamiast systemowego paska z nazwą."""
        self.verticalLayout_main.removeWidget(self.header_frame)
        self.setTitleBarWidget(self.header_frame)

    def _applyTheme(self, force=False) -> None:
        """Ustawia właściwość "theme" - kolory zdefiniowane w arkuszu stylów w pliku .ui."""
        theme = 'dark' if ThemeUtils.isDarkTheme() else 'light'
        if theme == self._theme and not force:
            return
        self._theme = theme
        self.setProperty('theme', theme)
        ThemeUtils.repolishAll(self)
        color = FOOTER_LINK_COLORS[theme]
        for lbl in (self.lbl_email, self.lbl_szkolenia):
            lbl.setText(re.sub(r'style="[^"]*"', 'style="text-decoration:underline; color:%s;"' % color, lbl.text()))
        # Logo w stopce: zielone na jasnym tle, białe na ciemnym.
        self._setFooterLogo(FOOTER_LOGOS[theme])

    def _setFooterLogo(self, filename, height=34) -> None:
        ThemeUtils.setLogo(self.lbl_logo, filename, height)

    def _fitHeightOnOpen(self) -> None:
        """Przy otwarciu panel dostaje wysokość całej treści (chwilowe minimum - okno główne musi zrobić miejsce),
        potem minimum jest zwalniane i panel można zmniejszyć (treść jest w obszarze przewijania)."""
        if getattr(self, '_heightFitted', False) or self.isFloating():
            return
        self._heightFitted = True
        frame = 2 * self.style().pixelMetric(QtWidgets.QStyle.PixelMetric.PM_DockWidgetFrameWidth, None, self)
        need = (self.header_frame.sizeHint().height() + self.content_widget.minimumSizeHint().height()
                + self.footer_frame.sizeHint().height() + frame)
        main_window = self.parentWidget()
        if isinstance(main_window, QtWidgets.QMainWindow):
            area = main_window.dockWidgetArea(self)
            others = [d for d in main_window.findChildren(QtWidgets.QDockWidget)
                      if d is not self and d.isVisible() and not d.isFloating()
                      and main_window.dockWidgetArea(d) == area and abs(d.x() - self.x()) < 5]
            room = self.height() + sum(d.height() - d.minimumSizeHint().height() for d in others)
            need = min(need, room)
        if need <= self.height():
            return
        self.setMinimumHeight(need)
        QTimer.singleShot(0, self._releaseMinimumHeight)

    def _releaseMinimumHeight(self) -> None:
        try:
            self.setMinimumHeight(0)
        except RuntimeError as e:  # panel usunięty zanim timer zdążył się wykonać
            MessageUtils.pushLogWarning(f"Panel usunięty przed zwolnieniem minimalnej wysokości (RuntimeError): {e}")
            return

    def changeEvent(self, event) -> None:
        # changeEvent przychodzi już w trakcie setupUi - wtedy _theme jeszcze nie istnieje
        if (event.type() in (QEvent.Type.PaletteChange, QEvent.Type.StyleChange)
                and getattr(self, '_theme', None) is not None):
            self._applyTheme()
        super().changeEvent(event)

    def _openHelp(self) -> None:
        url = self._readHomepage() or HOME_LINK
        QDesktopServices.openUrl(QUrl(url))

    @staticmethod
    def _readHomepage() -> str:
        """Adres strony wtyczki z metadata.txt; pusty tekst, gdy nie da się go odczytać."""
        parser = configparser.ConfigParser(interpolation=None)
        try:
            # brak pliku lub brak dostępu read() pomija sam (bez wyjątku)
            parser.read(os.path.join(PLUGIN_DIR, 'metadata.txt'), encoding='utf-8')
        except UnicodeDecodeError as e:
            MessageUtils.pushLogWarning(f"Nie można odczytać metadata.txt - złe kodowanie (UnicodeDecodeError): {e}")
            return ''
        except configparser.Error as e:
            MessageUtils.pushLogWarning(f"Błędny format metadata.txt ({type(e).__name__}): {e}")
            return ''
        # fallback - brak sekcji lub klucza nie rzuca wyjątku
        return parser.get('general', 'homepage', fallback='')

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
        self.pushMessageOverTable(" Aktualizacja usług...", "Pobieranie")

        # Ponowna próba pobrania danych z API, jeśli poprzednia się nie powiodła
        if len(self.content_manager.getCountryServicesCache()) == 0:
            if not self.content_manager.servicesCacheInit():
                error_message = ServiceAPI().checkServicesConnection(TABLE_CONNECTIONS_CHECK)
                if error_message is None:
                    error_message = MSG_SERVICES_UNAVAILABLE
                self.pushMessageOverTable("Brak dostępu do usług.", error_message)
                self.setEnabledRadiobuttons(True)
                return
        if not self.table_setup_task.run():  # SingleTaskManager(self.fetchServices, self.finishTableSetup)
            self.pushMessageOverTable(" Aktualizacja usług...", "Nieoczekiwany błąd.")

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
            error_message = ServiceAPI().checkServicesConnection(ADD_SERVICE_CONNECTIONS_CHECK)
            if error_message is None:
                # Pobranie danych z tabeli i dodanie usług do mapy
                proxy_model = self.services_table.model()
                selected_indexes = self.services_table.selectionModel().selectedRows()
                selected_service_type = self.getSelectedServiceType()
                self.content_manager.addServiceFromSelection(proxy_model, selected_indexes, selected_service_type)

            else:
                MessageUtils.pushMessageBoxWarning(
                    self,
                    'Ostrzeżenie',
                    f'{error_message}\nNie można dodać usług.',
                )
        finally:
            # Odblokowanie elementów okna
            self.setEnabledRadiobuttons(True)
            self.setEnabledTable(True)

    # =============================
    # Fukcje obsługujące elementy okna

    def fillServicesTable(self, service_rows: List = []) -> None:
        """Czyści tabelę i wypełnia na nowo danymi"""
        # przed zmianą wierszy - sygnały modelu od razu przeliczają licznik usług
        self._is_message_shown = False
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

    def pushMessageOverTable(self, message: str, status: str = '') -> None:
        """Czyści tabelę i wykorzysuje pierwsze pole jako miejsce na komunikat i opcjonalnie status"""
        # przed zmianą wierszy - sygnały modelu od razu przeliczają licznik usług
        self._is_message_shown = True
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

    def setEnabledRadiobuttons(self, is_enabled=True):
        """Ustawia dostępność radiobutton'ów"""
        for obj in RADIOBUTTONS_SERVICES:
            widget_obj = getattr(self, obj)
            widget_obj.setEnabled(is_enabled)

    def setEnabledTable(self, is_enabled=True):
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
        self._applyTheme()
        super().showEvent(event)
        # dopiero po pokazaniu znany jest właściwy devicePixelRatio (skalowanie 125-150%)
        self._setFooterLogo(FOOTER_LOGOS[self._theme])
        self._fitHeightOnOpen()
        if not self.is_window_shown:
            if not self.content_manager.servicesCacheInit():
                error_message = ServiceAPI().checkServicesConnection(TABLE_CONNECTIONS_CHECK)
                if error_message is None:
                    error_message = MSG_SERVICES_UNAVAILABLE
                MessageUtils.pushMessageBoxWarning(
                    self,
                    'Ostrzeżenie',
                    f'{error_message}\nNie można pobrać usług.',
                )
            self.is_window_shown = True
        self.setupTable()
        self.setEnabledRadiobuttons(True)
        self.setEnabledTable(True)
        self.wms_rdbtn.setFocus()

    def closeEvent(self, event: QShowEvent) -> None:
        self.is_window_shown = False
        self._heightFitted = False  # po ponownym otwarciu znowu pełna wysokość
        event.accept()
