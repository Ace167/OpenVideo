"""Settings view allowing user configuration of download, interface and logging options."""

from pathlib import Path

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from open_video_downloader.core.paths import get_app_data_dir, get_logs_dir
from open_video_downloader.settings.manager import SettingsManager
from open_video_downloader.settings.models import AppSettings


class SettingsPage(QWidget):
    """View allowing inspection and modification of application preferences."""

    settings_saved = Signal(AppSettings)

    def __init__(self, settings_manager: SettingsManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings_mgr = settings_manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        # 1. Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        title = QLabel("Instellingen", self)
        title.setProperty("class", "pageTitle")
        header_layout.addWidget(title)

        subtitle = QLabel(
            "Configureer downloadlocaties, interface-uiterlijk en diagnosevoorkeuren.", self
        )
        subtitle.setProperty("class", "pageSubtitle")
        header_layout.addWidget(subtitle)
        layout.addLayout(header_layout)

        # 2. Settings Card 1: Downloads
        dl_card = QFrame(self)
        dl_card.setProperty("class", "card")
        dl_layout = QVBoxLayout(dl_card)
        dl_layout.setSpacing(12)

        dl_header = QLabel("Downloads", self)
        dl_header.setProperty("class", "sectionHeader")
        dl_layout.addWidget(dl_header)

        # Download directory row
        dir_label = QLabel("Standaard downloadmap:", self)
        dl_layout.addWidget(dir_label)

        dir_row = QHBoxLayout()
        dir_row.setSpacing(10)
        self.download_dir_input = QLineEdit(self)
        dir_row.addWidget(self.download_dir_input, stretch=1)

        self.browse_btn = QPushButton("Bladeren...", self)
        self.browse_btn.setProperty("class", "btnSecondary")
        self.browse_btn.clicked.connect(self._on_browse_directory)
        dir_row.addWidget(self.browse_btn)
        dl_layout.addLayout(dir_row)

        # Concurrency row
        concur_row = QHBoxLayout()
        concur_label = QLabel("Maximum aantal gelijktijdige downloads:", self)
        concur_row.addWidget(concur_label)
        self.concurrency_spin = QSpinBox(self)
        self.concurrency_spin.setRange(1, 8)
        self.concurrency_spin.setFixedWidth(70)
        concur_row.addWidget(self.concurrency_spin)
        concur_row.addStretch()
        dl_layout.addLayout(concur_row)

        layout.addWidget(dl_card)

        # 3. Settings Card 2: Interface & Taal
        ui_card = QFrame(self)
        ui_card.setProperty("class", "card")
        ui_layout = QVBoxLayout(ui_card)
        ui_layout.setSpacing(12)

        ui_header = QLabel("Interface & Weergave", self)
        ui_header.setProperty("class", "sectionHeader")
        ui_layout.addWidget(ui_header)

        # Theme selection
        theme_row = QHBoxLayout()
        theme_label = QLabel("Thema:", self)
        theme_label.setFixedWidth(140)
        theme_row.addWidget(theme_label)

        self.theme_combo = QComboBox(self)
        self.theme_combo.addItem("Systeemthema volgen", "system")
        self.theme_combo.addItem("Donker thema", "dark")
        self.theme_combo.addItem("Licht thema", "light")
        self.theme_combo.setFixedWidth(200)
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch()
        ui_layout.addLayout(theme_row)

        # Language selection
        lang_row = QHBoxLayout()
        lang_label = QLabel("Interfacetaal:", self)
        lang_label.setFixedWidth(140)
        lang_row.addWidget(lang_label)

        self.lang_combo = QComboBox(self)
        self.lang_combo.addItem("Nederlands (nl)", "nl")
        self.lang_combo.addItem("English (en)", "en")
        self.lang_combo.setFixedWidth(200)
        lang_row.addWidget(self.lang_combo)
        lang_row.addStretch()
        ui_layout.addLayout(lang_row)

        # Notifications
        self.notif_check = QCheckBox(
            "Bureaubladmeldingen tonen wanneer een download gereed is", self
        )
        ui_layout.addWidget(self.notif_check)

        layout.addWidget(ui_card)

        # 4. Settings Card 3: Geavanceerd & Diagnose
        adv_card = QFrame(self)
        adv_card.setProperty("class", "card")
        adv_layout = QVBoxLayout(adv_card)
        adv_layout.setSpacing(12)

        adv_header = QLabel("Geavanceerd & Diagnose", self)
        adv_header.setProperty("class", "sectionHeader")
        adv_layout.addWidget(adv_header)

        log_row = QHBoxLayout()
        log_label = QLabel("Logniveau:", self)
        log_label.setFixedWidth(140)
        log_row.addWidget(log_label)

        self.log_combo = QComboBox(self)
        for lvl in ["INFO", "DEBUG", "WARNING", "ERROR"]:
            self.log_combo.addItem(lvl, lvl)
        self.log_combo.setFixedWidth(140)
        log_row.addWidget(self.log_combo)
        log_row.addStretch()
        adv_layout.addLayout(log_row)

        # Open storage buttons
        storage_row = QHBoxLayout()
        storage_row.setSpacing(10)

        self.open_data_btn = QPushButton("Open gebruikersdatamap", self)
        self.open_data_btn.setProperty("class", "btnSecondary")
        self.open_data_btn.clicked.connect(self._open_data_folder)
        storage_row.addWidget(self.open_data_btn)

        self.open_logs_btn = QPushButton("Open logmap", self)
        self.open_logs_btn.setProperty("class", "btnSecondary")
        self.open_logs_btn.clicked.connect(self._open_logs_folder)
        storage_row.addWidget(self.open_logs_btn)

        storage_row.addStretch()
        adv_layout.addLayout(storage_row)

        layout.addWidget(adv_card)

        # 5. Action Buttons & Feedback
        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        self.save_btn = QPushButton("Instellingen opslaan", self)
        self.save_btn.setProperty("class", "btnPrimary")
        self.save_btn.clicked.connect(self._save_settings)
        action_row.addWidget(self.save_btn)

        self.reset_btn = QPushButton("Standaardwaarden herstellen", self)
        self.reset_btn.setProperty("class", "btnSecondary")
        self.reset_btn.clicked.connect(self._reset_defaults)
        action_row.addWidget(self.reset_btn)

        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet("color: #16a34a; font-weight: 600; font-size: 12px;")
        action_row.addWidget(self.status_label)

        action_row.addStretch()
        layout.addLayout(action_row)

        layout.addStretch()

        # Populate with current settings
        self.load_from_manager()

    def load_from_manager(self) -> None:
        """Populate UI controls from currently active AppSettings."""
        s = self._settings_mgr.get()
        self.download_dir_input.setText(s.download_dir)
        self.concurrency_spin.setValue(s.max_concurrent_downloads)

        theme_idx = self.theme_combo.findData(s.theme)
        if theme_idx >= 0:
            self.theme_combo.setCurrentIndex(theme_idx)

        lang_idx = self.lang_combo.findData(s.language)
        if lang_idx >= 0:
            self.lang_combo.setCurrentIndex(lang_idx)

        self.notif_check.setChecked(s.notifications_enabled)

        log_idx = self.log_combo.findData(s.log_level)
        if log_idx >= 0:
            self.log_combo.setCurrentIndex(log_idx)

    def _on_browse_directory(self) -> None:
        """Open system directory picker for download location."""
        selected = QFileDialog.getExistingDirectory(
            self,
            "Selecteer downloadmap",
            self.download_dir_input.text() or str(Path.home()),
        )
        if selected:
            self.download_dir_input.setText(selected)

    def _save_settings(self) -> None:
        """Extract UI input, update SettingsManager and notify user."""
        download_dir = self.download_dir_input.text().strip()
        theme = str(self.theme_combo.currentData())
        lang = str(self.lang_combo.currentData())
        notif = self.notif_check.isChecked()
        log_lvl = str(self.log_combo.currentData())
        max_concurrent = self.concurrency_spin.value()

        new_settings = AppSettings(
            download_dir=download_dir,
            theme=theme,
            language=lang,
            notifications_enabled=notif,
            log_level=log_lvl,
            max_concurrent_downloads=max_concurrent,
        )

        success = self._settings_mgr.save_settings(new_settings)
        if success:
            self.status_label.setText("✓ Instellingen succesvol opgeslagen.")
            self.status_label.setStyleSheet("color: #16a34a; font-weight: 600; font-size: 12px;")
            self.settings_saved.emit(new_settings)
        else:
            self.status_label.setText("Fout bij opslaan van instellingen.")
            self.status_label.setStyleSheet("color: #e11d48; font-weight: 600; font-size: 12px;")

    def _reset_defaults(self) -> None:
        """Reset controls to standard factory defaults and save."""
        default_settings = AppSettings.create_default()
        self._settings_mgr.save_settings(default_settings)
        self.load_from_manager()
        self.status_label.setText("✓ Standaardwaarden hersteld.")
        self.status_label.setStyleSheet("color: #0284c7; font-weight: 600; font-size: 12px;")
        self.settings_saved.emit(default_settings)

    def _open_data_folder(self) -> None:
        """Open local user data folder in Windows Explorer."""
        data_dir = get_app_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(data_dir)))

    def _open_logs_folder(self) -> None:
        """Open local logs folder in Windows Explorer."""
        logs_dir = get_logs_dir()
        logs_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(logs_dir)))
