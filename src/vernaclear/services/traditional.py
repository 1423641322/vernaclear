from __future__ import annotations

import urllib.parse
import uuid

from vernaclear.core.config import TraditionalSettings
from vernaclear.core.models import ConfigurationError, ServiceError
from vernaclear.services.http import post_form, post_json


_DEEPL_CODES = {
    "zh-Hans": "ZH-HANS",
    "zh-Hant": "ZH-HANT",
    "en": "EN",
    "ja": "JA",
    "ko": "KO",
    "fr": "FR",
    "de": "DE",
    "es": "ES",
    "ru": "RU",
}


class TraditionalTranslator:
    def __init__(self, settings: TraditionalSettings) -> None:
        self.settings = settings

    @property
    def configured(self) -> bool:
        return bool(self.settings.api_key.strip())

    @property
    def display_name(self) -> str:
        return "DeepL" if self.settings.provider == "deepl" else "Microsoft Translator"

    def translate(self, text: str, source: str, target: str) -> str:
        if not self.configured:
            raise ConfigurationError("尚未配置传统翻译 API 密钥。请打开“设置”。")
        if self.settings.provider == "deepl":
            return self._translate_deepl(text, source, target)
        return self._translate_microsoft(text, source, target)

    def _translate_microsoft(self, text: str, source: str, target: str) -> str:
        base = self.settings.endpoint.strip().rstrip("/")
        if not base:
            base = "https://api.cognitive.microsofttranslator.com"
        params = {"api-version": "3.0", "to": target}
        if source != "auto":
            params["from"] = source
        url = f"{base}/translate?{urllib.parse.urlencode(params)}"
        headers = {
            "Ocp-Apim-Subscription-Key": self.settings.api_key.strip(),
            "X-ClientTraceId": str(uuid.uuid4()),
        }
        if self.settings.region.strip():
            headers["Ocp-Apim-Subscription-Region"] = self.settings.region.strip()
        response = post_json(url, [{"text": text}], headers=headers)
        try:
            return str(response[0]["translations"][0]["text"])
        except (KeyError, IndexError, TypeError) as error:
            raise ServiceError("Microsoft Translator 返回结果中没有译文。") from error

    def _translate_deepl(self, text: str, source: str, target: str) -> str:
        base = self.settings.endpoint.strip().rstrip("/")
        if not base or "microsofttranslator" in base:
            base = "https://api-free.deepl.com/v2"
        url = base if base.endswith("/translate") else f"{base}/translate"
        fields = {
            "text": text,
            "target_lang": _DEEPL_CODES.get(target, target.upper()),
        }
        if source != "auto":
            fields["source_lang"] = _DEEPL_CODES.get(source, source.upper())
        response = post_form(
            url,
            fields,
            headers={"Authorization": f"DeepL-Auth-Key {self.settings.api_key.strip()}"},
        )
        try:
            return str(response["translations"][0]["text"])
        except (KeyError, IndexError, TypeError) as error:
            raise ServiceError("DeepL 返回结果中没有译文。") from error

