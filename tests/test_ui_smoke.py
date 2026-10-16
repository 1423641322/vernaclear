import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from vernaclear.ui.main_window import MainWindow


def test_main_window_constructs() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    assert window.windowTitle() == "Vernaclear · 语境译"
    assert window.translate_button.isEnabled()
    window.close()
    app.processEvents()

