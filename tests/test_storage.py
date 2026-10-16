from pathlib import Path

from vernaclear.core.config import AppSettings, SettingsStore
from vernaclear.core.database import Database
from vernaclear.core.models import GlossaryEntry, TranslationMode, TranslationResult


def test_settings_roundtrip_encrypts_keys(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    settings = AppSettings()
    settings.ui_language = "en"
    settings.llm.api_key = "secret-llm-key"
    settings.traditional.api_key = "secret-traditional-key"
    store = SettingsStore(path)
    store.save(settings)
    raw = path.read_text(encoding="utf-8")
    assert "secret-llm-key" not in raw
    assert "secret-traditional-key" not in raw
    restored = store.load()
    assert restored.ui_language == "en"
    assert restored.llm.api_key == "secret-llm-key"
    assert restored.traditional.api_key == "secret-traditional-key"


def test_database_history_and_personal_glossary(tmp_path: Path) -> None:
    database = Database(tmp_path / "test.db")
    database.save_glossary_entry(GlossaryEntry("foo", "bar", "en", "personal"))
    assert database.glossary_entries()[0].expansion == "bar"
    database.add_history(
        TranslationResult("idk", "我不知道", "test", TranslationMode.LLM)
    )
    assert database.recent_context(1) == ["idk"]
    database.clear_history()
    assert database.recent_context(1) == []

