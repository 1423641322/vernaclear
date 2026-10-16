from __future__ import annotations

import ctypes
import json
import os
import sys
import traceback

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from vernaclear.core.paths import logs_dir, resource_path
from vernaclear.ui.main_window import MainWindow
from vernaclear.ui.theme import APP_STYLE


def _enable_windows_dpi_awareness() -> None:
    if os.name != "nt":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def main() -> int:
    _enable_windows_dpi_awareness()
    if "--self-test" in sys.argv:
        try:
            return _self_test()
        except Exception as error:
            output = logs_dir() / "self-test.json"
            output.write_text(
                json.dumps(
                    {
                        "status": "error",
                        "error": str(error),
                        "traceback": traceback.format_exc(),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            return 1
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setApplicationName("Vernaclear")
    app.setOrganizationName("Vernaclear")
    app.setApplicationVersion("0.1.0")
    icon_path = resource_path("icon.svg")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    app.setStyleSheet(APP_STYLE)
    window = MainWindow()
    window.show()
    return app.exec()


def _self_test() -> int:
    from vernaclear.core.lexicon import Lexicon
    from vernaclear.services.ocr import OcrService

    lexicon = Lexicon.from_json()
    expanded, matches = lexicon.expand("idk, ggwp")
    result: dict[str, object] = {
        "status": "ok",
        "lexicon": expanded,
        "matches": len(matches),
        "resources": str(resource_path("abbr_lexicon.json")),
    }
    try:
        index = sys.argv.index("--self-test")
        image_path = sys.argv[index + 1] if index + 1 < len(sys.argv) else ""
    except (ValueError, IndexError):
        image_path = ""
    if image_path:
        result["ocr"] = OcrService().recognize(image_path)
    output = logs_dir() / "self-test.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

