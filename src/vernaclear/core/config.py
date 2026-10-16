from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from vernaclear.core.paths import config_dir
from vernaclear.core.secrets import protect, unprotect


DEFAULT_LLM_PROMPT = """You are Vernaclear, a context-aware chat translator.
Translate the user's message into {target_language}.
Understand abbreviations, internet slang, gaming terms, phonetic spellings, code-switching, irony, and omitted words.
Use the supplied conversation context and glossary. Preserve tone without adding commentary.
If an abbreviation is genuinely ambiguous, choose the most likely meaning from context.
Return only the natural translation."""


@dataclass(slots=True)
class TraditionalSettings:
    provider: str = "microsoft"
    endpoint: str = "https://api.cognitive.microsofttranslator.com"
    api_key: str = ""
    region: str = ""


@dataclass(slots=True)
class LlmSettings:
    base_url: str = "http://localhost:11434/v1"
    api_key: str = ""
    model: str = ""
    temperature: float = 0.2
    system_prompt: str = DEFAULT_LLM_PROMPT


@dataclass(slots=True)
class AppSettings:
    source_language: str = "auto"
    target_language: str = "zh-Hans"
    default_mode: str = "hybrid"
    save_history: bool = True
    context_size: int = 8
    traditional: TraditionalSettings = field(default_factory=TraditionalSettings)
    llm: LlmSettings = field(default_factory=LlmSettings)


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or config_dir() / "settings.json"

    def load(self) -> AppSettings:
        if not self.path.exists():
            return AppSettings()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            traditional = raw.get("traditional", {})
            llm = raw.get("llm", {})
            traditional["api_key"] = unprotect(traditional.get("api_key", ""))
            llm["api_key"] = unprotect(llm.get("api_key", ""))
            return AppSettings(
                source_language=raw.get("source_language", "auto"),
                target_language=raw.get("target_language", "zh-Hans"),
                default_mode=raw.get("default_mode", "hybrid"),
                save_history=bool(raw.get("save_history", True)),
                context_size=max(0, min(30, int(raw.get("context_size", 8)))),
                traditional=TraditionalSettings(**traditional),
                llm=LlmSettings(**llm),
            )
        except (OSError, ValueError, TypeError):
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        payload = asdict(settings)
        payload["traditional"]["api_key"] = protect(settings.traditional.api_key)
        payload["llm"]["api_key"] = protect(settings.llm.api_key)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(self.path)

