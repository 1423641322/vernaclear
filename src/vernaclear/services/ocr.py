from __future__ import annotations

from pathlib import Path
from typing import Any

from vernaclear.core.models import OcrError


class OcrService:
    def __init__(self) -> None:
        self._engine: Any = None

    def _get_engine(self) -> Any:
        if self._engine is None:
            try:
                from rapidocr import RapidOCR

                self._engine = RapidOCR()
            except Exception as error:
                raise OcrError(f"OCR 引擎加载失败：{error}") from error
        return self._engine

    def recognize(self, image: str | Path) -> str:
        try:
            result = self._get_engine()(str(image))
        except Exception as error:
            raise OcrError(f"图片识别失败：{error}") from error

        texts: list[str] = []
        if hasattr(result, "txts"):
            texts = [str(text) for text in (result.txts or [])]
        elif isinstance(result, tuple) and result:
            rows = result[0] or []
            for row in rows:
                if len(row) >= 2:
                    value = row[1]
                    texts.append(str(value[0] if isinstance(value, (list, tuple)) else value))
        elif isinstance(result, list):
            for row in result:
                if isinstance(row, (list, tuple)) and len(row) >= 2:
                    value = row[1]
                    texts.append(str(value[0] if isinstance(value, (list, tuple)) else value))
        cleaned = "\n".join(text.strip() for text in texts if text and text.strip()).strip()
        if not cleaned:
            raise OcrError("没有在图片中识别到文字。请尝试选择更清晰或更大的区域。")
        return cleaned

