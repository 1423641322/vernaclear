from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThreadPool, QTimer, Qt
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from vernaclear.core.config import SettingsStore
from vernaclear.core.database import Database
from vernaclear.core.i18n import LANGUAGE_OPTIONS, MODE_OPTIONS, normalize_ui_language, tr
from vernaclear.core.lexicon import Lexicon
from vernaclear.core.models import TranslationMode, TranslationRequest, TranslationResult
from vernaclear.services.ocr import OcrService
from vernaclear.services.router import TranslationRouter
from vernaclear.ui.dialogs import GlossaryDialog, HistoryDialog, SettingsDialog
from vernaclear.ui.screenshot import ScreenSnipOverlay
from vernaclear.ui.worker import Worker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.resize(1180, 760)
        self.setMinimumSize(920, 620)
        self.settings_store = SettingsStore()
        self.settings = self.settings_store.load()
        self.locale = normalize_ui_language(self.settings.ui_language)
        self.database = Database()
        self.ocr = OcrService()
        self.thread_pool = QThreadPool.globalInstance()
        self._snip_overlay: ScreenSnipOverlay | None = None
        self._temporary_ocr_path: Path | None = None
        self._busy = False
        self._build_ui()
        self._apply_language()
        self._restore_settings()
        self._connect_shortcuts()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(20, 18, 20, 14)
        outer.setSpacing(14)

        header = QFrame()
        header.setObjectName("Header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 14, 16, 14)
        title_column = QVBoxLayout()
        self.brand_label = QLabel()
        self.brand_label.setObjectName("Brand")
        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("Subtitle")
        title_column.addWidget(self.brand_label)
        title_column.addWidget(self.subtitle_label)
        header_layout.addLayout(title_column)
        header_layout.addStretch()
        self.language_button = QPushButton()
        self.history_button = QPushButton()
        self.glossary_button = QPushButton()
        self.settings_button = QPushButton()
        header_layout.addWidget(self.language_button)
        header_layout.addWidget(self.history_button)
        header_layout.addWidget(self.glossary_button)
        header_layout.addWidget(self.settings_button)
        outer.addWidget(header)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        self.source_combo = QComboBox()
        self.target_combo = QComboBox()
        self.mode_combo = QComboBox()
        self.source_label = QLabel()
        self.method_label = QLabel()
        controls.addWidget(self.source_label)
        controls.addWidget(self.source_combo)
        controls.addWidget(QLabel("→"))
        controls.addWidget(self.target_combo)
        controls.addSpacing(14)
        controls.addWidget(self.method_label)
        controls.addWidget(self.mode_combo)
        controls.addStretch()
        self.import_button = QPushButton()
        self.snip_button = QPushButton()
        controls.addWidget(self.import_button)
        controls.addWidget(self.snip_button)
        outer.addLayout(controls)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_input_panel())
        splitter.addWidget(self._build_result_panel())
        splitter.setSizes([560, 560])
        outer.addWidget(splitter, 1)

        self.translate_button.clicked.connect(self._translate)
        self.copy_button.clicked.connect(self._copy_result)
        self.clear_button.clicked.connect(self._clear)
        self.import_button.clicked.connect(self._import_image)
        self.snip_button.clicked.connect(self._start_snip)
        self.settings_button.clicked.connect(self._open_settings)
        self.glossary_button.clicked.connect(self._open_glossary)
        self.history_button.clicked.connect(self._open_history)
        self.language_button.clicked.connect(self._toggle_language)
        self.source_combo.currentIndexChanged.connect(self._persist_ui_settings)
        self.target_combo.currentIndexChanged.connect(self._persist_ui_settings)
        self.mode_combo.currentIndexChanged.connect(self._persist_ui_settings)

    def _build_input_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        heading = QHBoxLayout()
        self.input_title_label = QLabel()
        self.input_title_label.setObjectName("SectionTitle")
        self.input_hint_label = QLabel()
        self.input_hint_label.setObjectName("Muted")
        heading.addWidget(self.input_title_label)
        heading.addStretch()
        heading.addWidget(self.input_hint_label)
        layout.addLayout(heading)
        self.input_edit = QTextEdit()
        self.input_edit.setAcceptRichText(False)
        layout.addWidget(self.input_edit, 1)
        actions = QHBoxLayout()
        self.clear_button = QPushButton()
        self.translate_button = QPushButton()
        self.translate_button.setObjectName("Primary")
        actions.addWidget(self.clear_button)
        actions.addStretch()
        actions.addWidget(self.translate_button)
        layout.addLayout(actions)
        return panel

    def _t(self, key: str, **values: object) -> str:
        return tr(self.locale, key, **values)

    def _populate_choices(self) -> None:
        source = self.source_combo.currentData() or self.settings.source_language
        target = self.target_combo.currentData() or self.settings.target_language
        mode = self.mode_combo.currentData() or self.settings.default_mode
        for combo in (self.source_combo, self.target_combo, self.mode_combo):
            combo.blockSignals(True)
            combo.clear()
        for code, label_key in LANGUAGE_OPTIONS:
            self.source_combo.addItem(self._t(label_key), code)
            if code != "auto":
                self.target_combo.addItem(self._t(label_key), code)
        for value, label_key in MODE_OPTIONS:
            self.mode_combo.addItem(self._t(label_key), value)
        self._select_data(self.source_combo, str(source))
        self._select_data(self.target_combo, str(target))
        self._select_data(self.mode_combo, str(mode))
        for combo in (self.source_combo, self.target_combo, self.mode_combo):
            combo.blockSignals(False)

    def _apply_language(self) -> None:
        self.setWindowTitle(self._t("window_title"))
        self.brand_label.setText(self._t("brand"))
        self.subtitle_label.setText(self._t("subtitle"))
        self.language_button.setText(self._t("switch_language"))
        self.history_button.setText(self._t("history"))
        self.glossary_button.setText(self._t("glossary"))
        self.settings_button.setText(self._t("settings"))
        self.source_label.setText(self._t("source"))
        self.method_label.setText(self._t("method"))
        self.import_button.setText(self._t("import_image"))
        self.snip_button.setText(self._t("snip"))
        self.input_title_label.setText(self._t("input_title"))
        self.input_hint_label.setText(self._t("input_hint"))
        self.input_edit.setPlaceholderText(self._t("input_placeholder"))
        self.clear_button.setText(self._t("clear"))
        self.translate_button.setText(self._t("processing") if self._busy else self._t("translate"))
        self.result_title_label.setText(self._t("result_title"))
        if not self.result_edit.toPlainText():
            self.provider_label.setText(self._t("waiting"))
        self.result_edit.setPlaceholderText(self._t("result_placeholder"))
        self.expressions_label.setText(self._t("expressions"))
        self.copy_button.setText(self._t("copy"))
        self._populate_choices()
        self.statusBar().showMessage(self._t("ready"))

    def _toggle_language(self) -> None:
        self.locale = "en" if self.locale == "zh" else "zh"
        self.settings.ui_language = self.locale
        self._apply_language()
        self._persist_ui_settings()

    def _build_result_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        heading = QHBoxLayout()
        self.result_title_label = QLabel()
        self.result_title_label.setObjectName("SectionTitle")
        self.provider_label = QLabel()
        self.provider_label.setObjectName("ProviderLabel")
        heading.addWidget(self.result_title_label)
        heading.addStretch()
        heading.addWidget(self.provider_label)
        layout.addLayout(heading)
        self.result_edit = QTextEdit()
        self.result_edit.setReadOnly(True)
        layout.addWidget(self.result_edit, 3)
        self.expressions_label = QLabel()
        self.expressions_label.setObjectName("SectionTitle")
        layout.addWidget(self.expressions_label)
        self.matches_list = QListWidget()
        self.matches_list.setMinimumHeight(130)
        self.matches_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.matches_list, 2)
        actions = QHBoxLayout()
        self.warning_label = QLabel("")
        self.warning_label.setObjectName("Muted")
        self.warning_label.setWordWrap(True)
        self.copy_button = QPushButton()
        actions.addWidget(self.warning_label, 1)
        actions.addWidget(self.copy_button)
        layout.addLayout(actions)
        return panel

    def _restore_settings(self) -> None:
        self._select_data(self.source_combo, self.settings.source_language)
        self._select_data(self.target_combo, self.settings.target_language)
        self._select_data(self.mode_combo, self.settings.default_mode)

    @staticmethod
    def _select_data(combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _connect_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self._translate)
        QShortcut(QKeySequence("Ctrl+Enter"), self, activated=self._translate)
        QShortcut(QKeySequence("Ctrl+Shift+A"), self, activated=self._start_snip)

    def _persist_ui_settings(self) -> None:
        self.settings.source_language = str(self.source_combo.currentData())
        self.settings.target_language = str(self.target_combo.currentData())
        self.settings.default_mode = str(self.mode_combo.currentData())
        self.settings.ui_language = self.locale
        try:
            self.settings_store.save(self.settings)
        except Exception as error:
            self.statusBar().showMessage(self._t("save_failed", error=error), 6000)

    def _build_lexicon(self) -> Lexicon:
        lexicon = Lexicon.from_json()
        for entry in self.database.glossary_entries():
            lexicon.add(entry)
        return lexicon

    def _translate(self) -> None:
        if self._busy:
            return
        text = self.input_edit.toPlainText().strip()
        if not text:
            QMessageBox.information(self, self._t("need_source_title"), self._t("need_source"))
            return
        try:
            mode = TranslationMode(str(self.mode_combo.currentData()))
        except ValueError:
            mode = TranslationMode.HYBRID
        request = TranslationRequest(
            text=text,
            source_language=str(self.source_combo.currentData()),
            target_language=str(self.target_combo.currentData()),
            mode=mode,
            context=self.database.recent_context(self.settings.context_size),
        )
        router = TranslationRouter(self.settings, self._build_lexicon())
        self._set_busy(True, self._t("translating"))
        worker = Worker(router.translate, request)
        worker.signals.completed.connect(self._show_result)
        worker.signals.failed.connect(self._show_error)
        worker.signals.finished.connect(lambda: self._set_busy(False))
        self.thread_pool.start(worker)

    def _show_result(self, result: object) -> None:
        if not isinstance(result, TranslationResult):
            self._show_error(self._t("bad_result"))
            return
        self.result_edit.setPlainText(result.translated)
        self.provider_label.setText(result.provider)
        self.warning_label.setText(result.warning)
        self.matches_list.clear()
        if not result.glossary_matches:
            self.matches_list.addItem(self._t("no_match"))
        else:
            seen: set[tuple[str, str]] = set()
            for match in result.glossary_matches:
                key = (match.source.casefold(), match.expansion)
                if key in seen:
                    continue
                seen.add(key)
                suffix = ""
                if match.alternatives:
                    separator = "; " if self.locale == "en" else "；"
                    suffix = f"  ·  {self._t('alternatives', items=separator.join(match.alternatives))}"
                if match.note:
                    suffix += f"  ·  {match.note}"
                self.matches_list.addItem(f"{match.source}  →  {match.expansion}{suffix}")
        if self.settings.save_history:
            self.database.add_history(result)
        self.statusBar().showMessage(self._t("translated", provider=result.provider), 5000)

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Vernaclear", message)
        self.statusBar().showMessage(message, 8000)

    def _set_busy(self, busy: bool, message: str = "") -> None:
        self._busy = busy
        self.translate_button.setDisabled(busy)
        self.import_button.setDisabled(busy)
        self.snip_button.setDisabled(busy)
        self.translate_button.setText(self._t("processing") if busy else self._t("translate"))
        if message:
            self.statusBar().showMessage(message)

    def _copy_result(self) -> None:
        text = self.result_edit.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.statusBar().showMessage(self._t("copied"), 3000)

    def _clear(self) -> None:
        self.input_edit.clear()
        self.result_edit.clear()
        self.matches_list.clear()
        self.provider_label.setText(self._t("waiting"))
        self.warning_label.clear()
        self.input_edit.setFocus()

    def _start_snip(self) -> None:
        if self._busy or self._snip_overlay is not None:
            return
        try:
            self._snip_overlay = ScreenSnipOverlay(self.locale)
            self._snip_overlay.captured.connect(self._ocr_capture)
            self._snip_overlay.failed.connect(self._show_error)
            self._snip_overlay.cancelled.connect(
                lambda: self.statusBar().showMessage(self._t("snip_cancelled"), 3000)
            )
            self._snip_overlay.destroyed.connect(self._release_snip)
            self._snip_overlay.start()
        except Exception as error:
            self._snip_overlay = None
            self._show_error(str(error))

    def _release_snip(self) -> None:
        self._snip_overlay = None

    def _import_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self._t("choose_image"),
            "",
            self._t("image_filter"),
        )
        if path:
            self._ocr_image(path)

    def _ocr_capture(self, path: str) -> None:
        self._temporary_ocr_path = Path(path)
        self._ocr_image(path)

    def _ocr_image(self, path: str) -> None:
        self._set_busy(True, self._t("ocr_working"))
        worker = Worker(self.ocr.recognize, Path(path))
        worker.signals.completed.connect(self._ocr_completed)
        worker.signals.failed.connect(self._show_error)
        worker.signals.finished.connect(self._ocr_finished)
        self.thread_pool.start(worker)

    def _ocr_finished(self) -> None:
        self._set_busy(False)
        temporary = self._temporary_ocr_path
        self._temporary_ocr_path = None
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    def _ocr_completed(self, text: object) -> None:
        self.input_edit.setPlainText(str(text))
        self.statusBar().showMessage(self._t("ocr_done"))
        QTimer.singleShot(0, self._translate)

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.settings = dialog.values(self.settings)
            try:
                self.settings_store.save(self.settings)
                self.statusBar().showMessage(self._t("settings_saved"), 4000)
            except Exception as error:
                self._show_error(self._t("save_failed", error=error))

    def _open_glossary(self) -> None:
        GlossaryDialog(self.database, self.locale, self).exec()

    def _open_history(self) -> None:
        HistoryDialog(self.database, self.locale, self).exec()

    def closeEvent(self, event: QCloseEvent) -> None:
        self._persist_ui_settings()
        event.accept()

