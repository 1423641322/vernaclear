from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    # PyInstaller exposes ``sys.frozen`` while Nuitka marks compiled modules
    # with ``__compiled__``.  Both builds must store portable data beside the
    # executable instead of inside the source tree.
    return bool(getattr(sys, "frozen", False) or "__compiled__" in globals())


def application_root() -> Path:
    portable_root = os.environ.get("VERNACLEAR_PORTABLE_ROOT", "").strip()
    if portable_root:
        return Path(portable_root).resolve()
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


def resource_root() -> Path:
    bundle = getattr(sys, "_MEIPASS", None)
    if bundle:
        return Path(bundle) / "vernaclear" / "resources"
    return Path(__file__).resolve().parents[1] / "resources"


def resource_path(name: str) -> Path:
    return resource_root() / name


def runtime_root() -> Path:
    portable = bool(os.environ.get("VERNACLEAR_PORTABLE_ROOT", "").strip())
    root = application_root() if is_frozen() or portable else application_root() / "runtime"
    root.mkdir(parents=True, exist_ok=True)
    return root


def config_dir() -> Path:
    path = runtime_root() / "config"
    path.mkdir(parents=True, exist_ok=True)
    return path


def data_dir() -> Path:
    path = runtime_root() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def logs_dir() -> Path:
    path = runtime_root() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path

