from __future__ import annotations

import json
import re
from pathlib import Path

from vernaclear.core.models import GlossaryEntry, GlossaryMatch
from vernaclear.core.paths import resource_path


_ASCII_TERM = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+'-]*$")


class Lexicon:
    def __init__(self, entries: list[GlossaryEntry] | None = None) -> None:
        self.entries = entries or []
        self._by_term = {entry.term.casefold(): entry for entry in self.entries}

    @classmethod
    def from_json(cls, path: Path | None = None) -> "Lexicon":
        source = path or resource_path("abbr_lexicon.json")
        data = json.loads(source.read_text(encoding="utf-8"))
        entries = [
            GlossaryEntry(
                term=item["term"],
                expansion=item["expansion"],
                language=item.get("language", "und"),
                category=item.get("category", "chat"),
                note=item.get("note", ""),
                alternatives=tuple(item.get("alternatives", [])),
            )
            for item in data
        ]
        return cls(entries)

    def add(self, entry: GlossaryEntry) -> None:
        self._by_term[entry.term.casefold()] = entry
        self.entries = list(self._by_term.values())

    @staticmethod
    def _pattern(term: str) -> re.Pattern[str]:
        escaped = re.escape(term)
        if _ASCII_TERM.match(term):
            return re.compile(rf"(?<![\w]){escaped}(?![\w])", re.IGNORECASE)
        return re.compile(escaped, re.IGNORECASE)

    def find(self, text: str) -> list[GlossaryMatch]:
        matches: list[tuple[int, GlossaryMatch]] = []
        occupied: list[tuple[int, int]] = []
        for entry in sorted(self._by_term.values(), key=lambda item: len(item.term), reverse=True):
            for found in self._pattern(entry.term).finditer(text):
                span = found.span()
                if any(span[0] < end and start < span[1] for start, end in occupied):
                    continue
                occupied.append(span)
                matches.append(
                    (
                        span[0],
                        GlossaryMatch(
                            source=found.group(0),
                            expansion=entry.expansion,
                            language=entry.language,
                            category=entry.category,
                            note=entry.note,
                            alternatives=entry.alternatives,
                        ),
                    )
                )
        return [match for _, match in sorted(matches, key=lambda item: item[0])]

    def expand(self, text: str) -> tuple[str, list[GlossaryMatch]]:
        found = self.find(text)
        expanded = text
        unique: dict[str, GlossaryMatch] = {}
        for match in found:
            unique.setdefault(match.source.casefold(), match)
        for match in sorted(unique.values(), key=lambda item: len(item.source), reverse=True):
            replacement = f"{match.source} ({match.expansion})"
            expanded = self._pattern(match.source).sub(replacement, expanded)
        return expanded, found

    def ambiguity_score(self, text: str) -> float:
        matches = self.find(text)
        if not matches:
            return 0.0
        ambiguous = sum(1 for item in matches if item.ambiguous)
        informal = sum(1 for item in matches if item.category in {"slang", "gaming", "meme"})
        return min(1.0, ambiguous * 0.55 + informal * 0.12)

