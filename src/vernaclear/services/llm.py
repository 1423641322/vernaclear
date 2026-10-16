from __future__ import annotations

from vernaclear.core.config import LlmSettings
from vernaclear.core.models import ConfigurationError, GlossaryMatch, ServiceError
from vernaclear.services.http import post_json


class LlmTranslator:
    def __init__(self, settings: LlmSettings) -> None:
        self.settings = settings

    @property
    def configured(self) -> bool:
        return bool(self.settings.base_url.strip() and self.settings.model.strip())

    @property
    def display_name(self) -> str:
        return f"大模型 · {self.settings.model.strip() or '未配置'}"

    def _endpoint(self) -> str:
        base = self.settings.base_url.strip().rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        return f"{base}/chat/completions"

    def translate(
        self,
        text: str,
        source: str,
        target: str,
        context: list[str],
        matches: list[GlossaryMatch],
    ) -> str:
        if not self.configured:
            raise ConfigurationError("尚未配置大模型地址和模型名称。请打开“设置”。")
        prompt = self.settings.system_prompt.format(
            source_language=source, target_language=target
        )
        glossary = "\n".join(
            f"- {item.source}: {item.expansion}"
            + (f"；可能的其他含义：{', '.join(item.alternatives)}" if item.alternatives else "")
            for item in matches
        )
        context_text = "\n".join(f"- {line}" for line in context if line.strip())
        user_content = (
            f"Source language: {source}\nTarget language: {target}\n"
            f"Conversation context:\n{context_text or '(none)'}\n\n"
            f"Matched glossary:\n{glossary or '(none)'}\n\n"
            f"Message to translate:\n{text}"
        )
        headers: dict[str, str] = {}
        if self.settings.api_key.strip():
            headers["Authorization"] = f"Bearer {self.settings.api_key.strip()}"
        response = post_json(
            self._endpoint(),
            {
                "model": self.settings.model.strip(),
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_content},
                ],
                "temperature": self.settings.temperature,
                "stream": False,
            },
            headers=headers,
            timeout=90.0,
        )
        try:
            content = response["choices"][0]["message"]["content"]
            if isinstance(content, list):
                content = "".join(
                    str(part.get("text", "")) if isinstance(part, dict) else str(part)
                    for part in content
                )
            translated = str(content).strip()
            if not translated:
                raise KeyError("empty content")
            return translated
        except (KeyError, IndexError, TypeError) as error:
            raise ServiceError("大模型接口返回结果中没有可用译文。") from error

