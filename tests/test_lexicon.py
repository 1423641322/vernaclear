from vernaclear.core.lexicon import Lexicon
from vernaclear.core.models import GlossaryEntry


def test_ascii_abbreviations_respect_word_boundaries() -> None:
    lexicon = Lexicon([GlossaryEntry("idk", "I don't know", "en")])
    expanded, matches = lexicon.expand("idk, but useridkvalue is unrelated")
    assert expanded == "idk (I don't know), but useridkvalue is unrelated"
    assert len(matches) == 1


def test_longer_terms_win_over_overlapping_terms() -> None:
    lexicon = Lexicon(
        [
            GlossaryEntry("gg", "good game", "en"),
            GlossaryEntry("ggwp", "good game, well played", "en"),
        ]
    )
    matches = lexicon.find("ggwp gg")
    assert [(item.source, item.expansion) for item in matches] == [
        ("ggwp", "good game, well played"),
        ("gg", "good game"),
    ]


def test_ambiguity_score_detects_ambiguous_chat_term() -> None:
    lexicon = Lexicon(
        [GlossaryEntry("fr", "for real", "en", "slang", alternatives=("French",))]
    )
    assert lexicon.ambiguity_score("fr this is wild") >= 0.45


def test_unicode_terms_are_matched() -> None:
    lexicon = Lexicon([GlossaryEntry("ㅋㅋ", "哈哈", "ko", "slang")])
    expanded, matches = lexicon.expand("진짜ㅋㅋ")
    assert "ㅋㅋ (哈哈)" in expanded
    assert len(matches) == 1

