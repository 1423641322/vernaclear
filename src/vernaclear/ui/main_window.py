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
from vernaclear.core.lexicon import Lexicon
from vernaclear.core.models import TranslationMode, TranslationRequest, TranslationResult
from vernaclear.services.ocr import OcrService
from vernaclear.services.router import TranslationRouter
from vernaclear.ui.dialogs import GlossaryDialog, HistoryDialog, SettingsDialog
from vernaclear.ui.screenshot import ScreenSnipOverlay
from vernaclear.ui.worker import Worker


LANGUAGES = [
    ("自动检测", "auto"),
    ("简体中文", "zh-Hans"),
    ("繁体中文", "zh-Hant"),
    ("英语", "en"),
    ("日语", "ja"),
    ("韩语", "ko"),
    ("法语", "fr"),
    ("德语", "de"),
    ("西班牙语", "es"),
    ("俄语", "ru"),
]

MODES = [
    ("智能混合", TranslationMode.HYBRID.value),
    ("词库 + 传统翻译", TranslationMode.TRADITIONAL.value),
    ("上下文大模型", TranslationMode.LLM.value),
]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Vernaclear · 语境译")
        self.resize(1180, 760)
        self.setMinimumSize(920, 620)
        self.settings_store = SettingsStore()
        self.settings = self.settings_store.load()
        self.database = Database()
        self.ocr = OcrService()
        self.thread_pool = QThreadPool.globalInstance()
        self._snip_overlay: ScreenSnipOverlay | None = None
        self._busy = False
        self._build_ui()
        self._restore_settings()
        self._connect_shortcuts()
        self.statusBar().showMessage("就绪 · OCR 在本地运行，截图默认不保存到历史目录")

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
        brand = QLabel("Vernaclear  ·  语境译")
        brand.setObjectName("Brand")
        subtitle = QLabel("看懂聊天里的每一种说法")
        subtitle.setObjectName("Subtitle")
        title_column.addWidget(brand)
        title_column.addWidget(subtitle)
        header_layout.addLayout(title_column)
        header_layout.addStretch()
        self.history_button = QPushButton("历史")
        self.glossary_button = QPushButton("个人词库")
        self.settings_button = QPushButton("设置")
        header_layout.addWidget(self.history_button)
        header_layout.addWidget(self.glossary_button)
        header_layout.addWidget(self.settings_button)
        outer.addWidget(header)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        self.source_combo = QComboBox()
        self.target_combo = QComboBox()
        for label, code in LANGUAGES:
            self.source_combo.addItem(label, code)
            if code != "auto":
                self.target_combo.addItem(label, code)
        self.mode_combo = QComboBox()
        for label, mode in MODES:
            self.mode_combo.addItem(label, mode)
        controls.addWidget(QLabel("原文"))
        controls.addWidget(self.source_combo)
        controls.addWidget(QLabel("→"))
        controls.addWidget(self.target_combo)
        controls.addSpacing(14)
        controls.addWidget(QLabel("翻译方式"))
        controls.addWidget(self.mode_combo)
        controls.addStretch()
        self.import_button = QPushButton("导入图片")
        self.snip_button = QPushButton("框选截图  Ctrl+Shift+A")
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
        self.source_combo.currentIndexChanged.connect(self._persist_ui_settings)
        self.target_combo.currentIndexChanged.connect(self._persist_ui_settings)
        self.mode_combo.currentIndexChanged.connect(self._persist_ui_settings)

    def _build_input_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        heading = QHBoxLayout()
        title = QLabel("原文 / OCR 结果")
        title.setObjectName("SectionTitle")
        hint = QLabel("支持粘贴真实聊天内容")
        hint.setObjectName("Muted")
        heading.addWidget(title)
        heading.addStretch()
        heading.addWidget(hint)
        layout.addLayout(heading)
        self.input_edit = QTextEdit()
        self.input_edit.setAcceptRichText(False)
        self.input_edit.setPlaceholderText(
            "输入或粘贴聊天内容，例如：\nngl that build is kinda OP rn, gg!\n\n也可以点击“框选截图”或“导入图片”。"
        )
        layout.addWidget(self.input_edit, 1)
        actions = QHBoxLayout()
        self.clear_button = QPushButton("清空")
        self.translate_button = QPushButton("开始翻译  Ctrl+Enter")
        self.translate_button.setObjectName("Primary")
        actions.addWidget(self.clear_button)
        actions.addStretch()
        actions.addWidget(self.translate_button)
        layout.addLayout(actions)
        return panel

    def _build_result_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        heading = QHBoxLayout()
        title = QLabel("自然译文")
        title.setObjectName("SectionTitle")
        self.provider_label = QLabel("等待翻译")
        self.provider_label.setObjectName("ProviderLabel")
        heading.addWidget(title)
        heading.addStretch()
        heading.addWidget(self.provider_label)
        layout.addLayout(heading)
        self.result_edit = QTextEdit()
        self.result_edit.setReadOnly(True)
        self.result_edit.setPlaceholderText("译文将在这里显示。")
        layout.addWidget(self.result_edit, 3)
        glossary_header = QLabel("识别到的聊天表达")
        glossary_header.setObjectName("SectionTitle")
        layout.addWidget(glossary_header)
        self.matches_list = QListWidget()
        self.matches_list.setMinimumHeight(130)
        self.matches_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.matches_list, 2)
        actions = QHBoxLayout()
        self.warning_label = QLabel("")
        self.warning_label.setObjectName("Muted")
        self.warning_label.setWordWrap(True)
        self.copy_button = QPushButton("复制译文")
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
        try:
            self.settings_store.save(self.settings)
        except Exception as error:
            self.statusBar().showMessage(f"设置保存失败：{error}", 6000)

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
            QMessageBox.information(self, "需要原文", "请先输入文字、粘贴内容或进行截图识别。")
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
        self._set_busy(True, "正在理解聊天语境并翻译…")
        worker = Worker(router.translate, request)
        worker.signals.completed.connect(self._show_result)
        worker.signals.failed.connect(self._show_error)
        worker.signals.finished.connect(lambda: self._set_busy(False))
        self.thread_pool.start(worker)

    def _show_result(self, result: object) -> None:
        if not isinstance(result, TranslationResult):
            self._show_error("翻译结果格式异常。")
            return
        self.result_edit.setPlainText(result.translated)
        self.provider_label.setText(result.provider)
        self.warning_label.setText(result.warning)
        self.matches_list.clear()
        if not result.glossary_matches:
            self.matches_list.addItem("未匹配到内置或个人缩写词条")
        else:
            seen: set[tuple[str, str]] = set()
            for match in result.glossary_matches:
                key = (match.source.casefold(), match.expansion)
                if key in seen:
                    continue
                seen.add(key)
                suffix = ""
                if match.alternatives:
                    suffix = f"  ·  其他可能：{'；'.join(match.alternatives)}"
                if match.note:
                    suffix += f"  ·  {match.note}"
                self.matches_list.addItem(f"{match.source}  →  {match.expansion}{suffix}")
        if self.settings.save_history:
            self.database.add_history(result)
        self.statusBar().showMessage(f"翻译完成 · {result.provider}", 5000)

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Vernaclear", message)
        self.statusBar().showMessage(message, 8000)

    def _set_busy(self, busy: bool, message: str = "") -> None:
        self._busy = busy
        self.translate_button.setDisabled(busy)
        self.import_button.setDisabled(busy)
        self.snip_button.setDisabled(busy)
        self.translate_button.setText("处理中…" if busy else "开始翻译  Ctrl+Enter")
        if message:
            self.statusBar().showMessage(message)

    def _copy_result(self) -> None:
        text = self.result_edit.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.statusBar().showMessage("译文已复制到剪贴板", 3000)

    def _clear(self) -> None:
        self.input_edit.clear()
        self.result_edit.clear()
        self.matches_list.clear()
        self.provider_label.setText("等待翻译")
        self.warning_label.clear()
        self.input_edit.setFocus()

    def _start_snip(self) -> None:
        if self._busy or self._snip_overlay is not None:
            return
        try:
            self._snip_overlay = ScreenSnipOverlay()
            self._snip_overlay.captured.connect(self._ocr_image)
            self._snip_overlay.failed.connect(self._show_error)
            self._snip_overlay.cancelled.connect(lambda: self.statusBar().showMessage("已取消截图", 3000))
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
            "选择需要识别的图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff)",
        )
        if path:
            self._ocr_image(path)

    def _ocr_image(self, path: str) -> None:
        self._set_busy(True, "正在本地识别图片文字，首次加载模型可能较慢…")
        worker = Worker(self.ocr.recognize, Path(path))
        worker.signals.completed.connect(self._ocr_completed)
        worker.signals.failed.connect(self._show_error)
        worker.signals.finished.connect(lambda: self._set_busy(False))
        self.thread_pool.start(worker)

    def _ocr_completed(self, text: object) -> None:
        self.input_edit.setPlainText(str(text))
        self.statusBar().showMessage("OCR 完成，正在翻译…")
        QTimer.singleShot(0, self._translate)

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.settings = dialog.values(self.settings)
            try:
                self.settings_store.save(self.settings)
                self.statusBar().showMessage("设置已保存", 4000)
            except Exception as error:
                self._show_error(f"设置保存失败：{error}")

    def _open_glossary(self) -> None:
        GlossaryDialog(self.database, self).exec()

    def _open_history(self) -> None:
        HistoryDialog(self.database, self).exec()

    def closeEvent(self, event: QCloseEvent) -> None:
        self._persist_ui_settings()
        event.accept()

