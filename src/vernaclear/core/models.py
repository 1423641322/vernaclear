from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class TranslationMode(StrEnum):
    TRADITIONAL = "traditional"
    LLM = "llm"
    HYBRID = "hybrid"


@dataclass(slots=True, frozen=True)
class GlossaryEntry:
    term: str
    expansion: str
    language: str
    category: str = "chat"
    note: str = ""
    alternatives: tuple[str, ...] = ()

    @property
    def ambiguous(self) -> bool:
        return bool(self.alternatives)


@dataclass(slots=True, frozen=True)
class GlossaryMatch:
    source: str
    expansion: str
    language: str
    category: str
    note: str = ""
    alternatives: tuple[str, ...] = ()

    @property
    def ambiguous(self) -> bool:
        return bool(self.alternatives)


@dataclass(slots=True)
class TranslationRequest:
    text: str
    source_language: str = "auto"
    target_language: str = "zh-Hans"
    mode: TranslationMode = TranslationMode.HYBRID
    context: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TranslationResult:
    original: str
    translated: str
    provider: str
    mode_used: TranslationMode
    glossary_matches: list[GlossaryMatch] = field(default_factory=list)
    warning: str = ""


class VernaclearError(RuntimeError):
    """Base error suitable for presentation in the UI."""


class ConfigurationError(VernaclearError):
    """Raised when a provider is not configured."""


class ServiceError(VernaclearError):
    """Raised when a remote service returns an error."""


class OcrError(VernaclearError):
    """Raised when OCR cannot process an image."""

