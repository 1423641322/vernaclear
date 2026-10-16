import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from vernaclear.ui.main_window import MainWindow


def test_main_window_constructs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("VERNACLEAR_PORTABLE_ROOT", str(tmp_path))
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    assert window.windowTitle() == "Vernaclear · 语境译"
    assert window.translate_button.isEnabled()
    window.language_button.click()
    assert window.windowTitle() == "Vernaclear · Context Translator"
    assert window.translate_button.text().startswith("Translate")
    window.language_button.click()
    assert window.windowTitle() == "Vernaclear · 语境译"
    capture = tmp_path / "capture.png"
    capture.write_bytes(b"temporary")
    window._temporary_ocr_path = capture
    window._ocr_finished()
    assert not capture.exists()
    window.close()
    app.processEvents()

