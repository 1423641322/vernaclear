from vernaclear.core.i18n import TEXT, normalize_ui_language, tr


def test_translation_catalogs_have_matching_keys() -> None:
    assert set(TEXT["zh"]) == set(TEXT["en"])


def test_language_normalization_and_fallback() -> None:
    assert normalize_ui_language("en-US") == "en"
    assert normalize_ui_language("zh-Hans") == "zh"
    assert tr("en", "settings") == "Settings"
    assert tr("unsupported", "settings") == "设置"
