from __future__ import annotations

import base64
import ctypes
import os
from ctypes import wintypes


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _blob(data: bytes) -> tuple[_DataBlob, ctypes.Array]:
    buffer = ctypes.create_string_buffer(data)
    return _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char))), buffer


def protect(value: str) -> str:
    if not value:
        return ""
    if os.name != "nt":
        return "plain:" + base64.b64encode(value.encode("utf-8")).decode("ascii")
    source, source_buffer = _blob(value.encode("utf-8"))
    result = _DataBlob()
    ok = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(source),
        ctypes.c_wchar_p("Vernaclear API key"),
        None,
        None,
        None,
        0,
        ctypes.byref(result),
    )
    _ = source_buffer
    if not ok:
        raise ctypes.WinError()
    try:
        encrypted = ctypes.string_at(result.pbData, result.cbData)
        return "dpapi:" + base64.b64encode(encrypted).decode("ascii")
    finally:
        ctypes.windll.kernel32.LocalFree(result.pbData)


def unprotect(value: str) -> str:
    if not value:
        return ""
    if value.startswith("plain:"):
        return base64.b64decode(value[6:]).decode("utf-8")
    if not value.startswith("dpapi:") or os.name != "nt":
        return ""
    encrypted = base64.b64decode(value[6:])
    source, source_buffer = _blob(encrypted)
    result = _DataBlob()
    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(source), None, None, None, None, 0, ctypes.byref(result)
    )
    _ = source_buffer
    if not ok:
        return ""
    try:
        return ctypes.string_at(result.pbData, result.cbData).decode("utf-8")
    finally:
        ctypes.windll.kernel32.LocalFree(result.pbData)

