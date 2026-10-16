from __future__ import annotations

from vernaclear.core.config import AppSettings
from vernaclear.core.lexicon import Lexicon
from vernaclear.core.models import (
    ConfigurationError,
    TranslationMode,
    TranslationRequest,
    TranslationResult,
)
from vernaclear.services.llm import LlmTranslator
from vernaclear.services.traditional import TraditionalTranslator


class TranslationRouter:
    def __init__(self, settings: AppSettings, lexicon: Lexicon) -> None:
        self.settings = settings
        self.lexicon = lexicon
        self.traditional = TraditionalTranslator(settings.traditional)
        self.llm = LlmTranslator(settings.llm)

    def translate(self, request: TranslationRequest) -> TranslationResult:
        original = request.text.strip()
        if not original:
            raise ValueError("请输入需要翻译的文字。")
        expanded, matches = self.lexicon.expand(original)
        if request.mode == TranslationMode.TRADITIONAL:
            translated = self.traditional.translate(
                expanded, request.source_language, request.target_language
            )
            return TranslationResult(
                original, translated, self.traditional.display_name, request.mode, matches
            )
        if request.mode == TranslationMode.LLM:
            translated = self.llm.translate(
                original,
                request.source_language,
                request.target_language,
                request.context,
                matches,
            )
            return TranslationResult(original, translated, self.llm.display_name, request.mode, matches)

        score = self.lexicon.ambiguity_score(original)
        should_use_llm = self.llm.configured and (score >= 0.45 or not self.traditional.configured)
        if should_use_llm:
            translated = self.llm.translate(
                original,
                request.source_language,
                request.target_language,
                request.context,
                matches,
            )
            return TranslationResult(
                original, translated, self.llm.display_name, TranslationMode.LLM, matches
            )
        if self.traditional.configured:
            translated = self.traditional.translate(
                expanded, request.source_language, request.target_language
            )
            return TranslationResult(
                original,
                translated,
                self.traditional.display_name,
                TranslationMode.TRADITIONAL,
                matches,
            )
        if self.llm.configured:
            translated = self.llm.translate(
                original,
                request.source_language,
                request.target_language,
                request.context,
                matches,
            )
            return TranslationResult(
                original, translated, self.llm.display_name, TranslationMode.LLM, matches
            )
        if matches:
            return TranslationResult(
                original=original,
                translated=expanded,
                provider="本地缩写词库",
                mode_used=TranslationMode.HYBRID,
                glossary_matches=matches,
                warning="未配置翻译服务，当前仅展示缩写展开结果。",
            )
        raise ConfigurationError(
            "尚未配置可用的翻译服务。请在“设置”中填写传统翻译密钥或大模型接口。"
        )

