from vernaclear.core.config import AppSettings
from vernaclear.core.lexicon import Lexicon
from vernaclear.core.models import GlossaryEntry, TranslationMode, TranslationRequest
from vernaclear.services.router import TranslationRouter


def test_hybrid_without_provider_still_expands_known_abbreviation() -> None:
    settings = AppSettings()
    lexicon = Lexicon([GlossaryEntry("brb", "be right back", "en")])
    router = TranslationRouter(settings, lexicon)
    result = router.translate(TranslationRequest("brb", mode=TranslationMode.HYBRID))
    assert result.translated == "brb (be right back)"
    assert result.provider == "本地缩写词库"
    assert result.warning


def test_hybrid_routes_ambiguous_term_to_configured_llm(monkeypatch) -> None:
    settings = AppSettings()
    settings.llm.model = "test-model"
    lexicon = Lexicon(
        [GlossaryEntry("fr", "for real", "en", "slang", alternatives=("French",))]
    )
    router = TranslationRouter(settings, lexicon)
    monkeypatch.setattr(router.llm, "translate", lambda *args, **kwargs: "说真的")
    result = router.translate(TranslationRequest("fr", mode=TranslationMode.HYBRID))
    assert result.translated == "说真的"
    assert result.mode_used == TranslationMode.LLM


def test_traditional_receives_expanded_text(monkeypatch) -> None:
    settings = AppSettings()
    settings.traditional.api_key = "test"
    lexicon = Lexicon([GlossaryEntry("idk", "I don't know", "en")])
    router = TranslationRouter(settings, lexicon)
    captured = {}

    def fake_translate(text, source, target):
        captured["text"] = text
        return "我不知道"

    monkeypatch.setattr(router.traditional, "translate", fake_translate)
    result = router.translate(
        TranslationRequest("idk", mode=TranslationMode.TRADITIONAL)
    )
    assert captured["text"] == "idk (I don't know)"
    assert result.translated == "我不知道"

