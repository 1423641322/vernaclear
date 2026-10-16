from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from vernaclear.core.config import AppSettings, LlmSettings, TraditionalSettings
from vernaclear.core.database import Database
from vernaclear.core.i18n import normalize_ui_language, tr
from vernaclear.core.models import GlossaryEntry


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.locale = normalize_ui_language(settings.ui_language)
        self._t = lambda key, **values: tr(self.locale, key, **values)
        self.setWindowTitle(self._t("settings_title"))
        self.resize(720, 620)
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs)

        general = QWidget()
        general_form = QFormLayout(general)
        self.context_size = QSpinBox()
        self.context_size.setRange(0, 30)
        self.context_size.setValue(settings.context_size)
        general_form.addRow(self._t("context_count"), self.context_size)
        info = QLabel(self._t("privacy_note"))
        info.setWordWrap(True)
        info.setObjectName("Muted")
        general_form.addRow(self._t("privacy"), info)
        tabs.addTab(general, self._t("general"))

        traditional = QWidget()
        traditional_form = QFormLayout(traditional)
        self.traditional_provider = QComboBox()
        self.traditional_provider.addItem("Microsoft Translator", "microsoft")
        self.traditional_provider.addItem("DeepL", "deepl")
        self.traditional_provider.setCurrentIndex(
            max(0, self.traditional_provider.findData(settings.traditional.provider))
        )
        self.traditional_endpoint = QLineEdit(settings.traditional.endpoint)
        self.traditional_key = QLineEdit(settings.traditional.api_key)
        self.traditional_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.traditional_region = QLineEdit(settings.traditional.region)
        traditional_form.addRow(self._t("provider"), self.traditional_provider)
        traditional_form.addRow(self._t("api_endpoint"), self.traditional_endpoint)
        traditional_form.addRow(self._t("api_key"), self.traditional_key)
        traditional_form.addRow(self._t("azure_region"), self.traditional_region)
        self.traditional_provider.currentIndexChanged.connect(self._provider_changed)
        tabs.addTab(traditional, self._t("traditional_tab"))

        llm = QWidget()
        llm_form = QFormLayout(llm)
        self.llm_url = QLineEdit(settings.llm.base_url)
        self.llm_key = QLineEdit(settings.llm.api_key)
        self.llm_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.llm_model = QLineEdit(settings.llm.model)
        self.llm_model.setPlaceholderText(self._t("model_hint"))
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setSingleStep(0.1)
        self.temperature.setValue(settings.llm.temperature)
        self.system_prompt = QPlainTextEdit(settings.llm.system_prompt)
        self.system_prompt.setMinimumHeight(180)
        llm_form.addRow("Base URL", self.llm_url)
        llm_form.addRow(self._t("local_key"), self.llm_key)
        llm_form.addRow(self._t("model"), self.llm_model)
        llm_form.addRow("Temperature", self.temperature)
        llm_form.addRow(self._t("system_prompt"), self.system_prompt)
        tabs.addTab(llm, self._t("llm_tab"))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(self._t("save"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self._t("cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _provider_changed(self) -> None:
        provider = self.traditional_provider.currentData()
        current = self.traditional_endpoint.text().strip()
        if provider == "deepl" and (not current or "microsofttranslator" in current):
            self.traditional_endpoint.setText("https://api-free.deepl.com/v2")
        elif provider == "microsoft" and (not current or "deepl.com" in current):
            self.traditional_endpoint.setText("https://api.cognitive.microsofttranslator.com")

    def values(self, original: AppSettings) -> AppSettings:
        return AppSettings(
            ui_language=original.ui_language,
            source_language=original.source_language,
            target_language=original.target_language,
            default_mode=original.default_mode,
            save_history=original.save_history,
            context_size=self.context_size.value(),
            traditional=TraditionalSettings(
                provider=str(self.traditional_provider.currentData()),
                endpoint=self.traditional_endpoint.text().strip(),
                api_key=self.traditional_key.text().strip(),
                region=self.traditional_region.text().strip(),
            ),
            llm=LlmSettings(
                base_url=self.llm_url.text().strip(),
                api_key=self.llm_key.text().strip(),
                model=self.llm_model.text().strip(),
                temperature=self.temperature.value(),
                system_prompt=self.system_prompt.toPlainText().strip(),
            ),
        )


class GlossaryDialog(QDialog):
    def __init__(self, database: Database, language: str = "zh", parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.locale = normalize_ui_language(language)
        self._t = lambda key, **values: tr(self.locale, key, **values)
        self.setWindowTitle(self._t("glossary_title"))
        self.resize(780, 520)
        layout = QVBoxLayout(self)
        note = QLabel(self._t("glossary_note"))
        note.setWordWrap(True)
        note.setObjectName("Muted")
        layout.addWidget(note)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            [self._t("term"), self._t("meaning"), self._t("language"), self._t("note")]
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        controls = QHBoxLayout()
        add_button = QPushButton(self._t("add_row"))
        delete_button = QPushButton(self._t("delete_selected"))
        delete_button.setObjectName("Danger")
        save_button = QPushButton(self._t("save_glossary"))
        save_button.setObjectName("Primary")
        close_button = QPushButton(self._t("close"))
        controls.addWidget(add_button)
        controls.addWidget(delete_button)
        controls.addStretch()
        controls.addWidget(save_button)
        controls.addWidget(close_button)
        layout.addLayout(controls)
        add_button.clicked.connect(self._add_row)
        delete_button.clicked.connect(self._delete_selected)
        save_button.clicked.connect(self._save)
        close_button.clicked.connect(self.accept)
        self._load()

    def _load(self) -> None:
        for entry in self.database.glossary_entries():
            self._add_row(entry)

    def _add_row(self, entry: GlossaryEntry | None = None) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        values = (
            entry.term if entry else "",
            entry.expansion if entry else "",
            entry.language if entry else "und",
            entry.note if entry else "",
        )
        for column, value in enumerate(values):
            self.table.setItem(row, column, QTableWidgetItem(value))
        self.table.setCurrentCell(row, 0)

    def _delete_selected(self) -> None:
        rows = sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            item = self.table.item(row, 0)
            if item and item.text().strip():
                self.database.delete_glossary_entry(item.text().strip())
            self.table.removeRow(row)

    def _save(self) -> None:
        saved = 0
        for row in range(self.table.rowCount()):
            values = [
                self.table.item(row, column).text().strip()
                if self.table.item(row, column)
                else ""
                for column in range(4)
            ]
            if not values[0] or not values[1]:
                continue
            self.database.save_glossary_entry(
                GlossaryEntry(values[0], values[1], values[2] or "und", "personal", values[3])
            )
            saved += 1
        QMessageBox.information(
            self, self._t("glossary_title"), self._t("saved_entries", count=saved)
        )


class HistoryDialog(QDialog):
    def __init__(self, database: Database, language: str = "zh", parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.locale = normalize_ui_language(language)
        self._t = lambda key, **values: tr(self.locale, key, **values)
        self.setWindowTitle(self._t("history_title"))
        self.resize(900, 560)
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            [self._t("time"), self._t("original"), self._t("translation"), self._t("service")]
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        controls = QHBoxLayout()
        clear_button = QPushButton(self._t("clear_history"))
        clear_button.setObjectName("Danger")
        close_button = QPushButton(self._t("close"))
        controls.addWidget(clear_button)
        controls.addStretch()
        controls.addWidget(close_button)
        layout.addLayout(controls)
        clear_button.clicked.connect(self._clear)
        close_button.clicked.connect(self.accept)
        self._load()

    def _load(self) -> None:
        self.table.setRowCount(0)
        for record in self.database.recent_history():
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = (record["created_at"], record["original"], record["translated"], record["provider"])
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                self.table.setItem(row, column, item)

    def _clear(self) -> None:
        answer = QMessageBox.question(
            self, self._t("clear_history"), self._t("confirm_clear")
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.database.clear_history()
            self._load()

