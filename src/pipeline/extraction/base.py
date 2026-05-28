"""Abstract base + registry for geometry extractors."""
from __future__ import annotations

import json
import time as _time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from .schema import PanelGeometry, derive_archetype_booleans
from .splitter import SubPanelChunk


@dataclass
class ExtractionResult:
    geometry: PanelGeometry | None
    latency_sec: float
    cost_usd: float | None
    raw_response: str
    error: str | None


class Extractor(ABC):
    name: str = "abstract"

    @abstractmethod
    def _call(self, chunk: SubPanelChunk, prompt: str, system: str) -> tuple[str, float | None]:
        """Return (raw_text_response, cost_usd)."""

    def extract(self, chunk: SubPanelChunk) -> ExtractionResult:
        from .prompt import SYSTEM_PROMPT, build_user_prompt
        prompt = build_user_prompt(
            panel_id=chunk.panel_id,
            is_id=chunk.is_id,
            project_id=chunk.project_id,
            drawing_revision=chunk.drawing_revision,
        )
        t0 = _time.perf_counter()
        try:
            raw, cost = self._call(chunk, prompt, SYSTEM_PROMPT)
        except Exception as e:
            return ExtractionResult(None, _time.perf_counter() - t0, None, "", f"{type(e).__name__}: {e}")
        latency = _time.perf_counter() - t0

        # Strip possible ```json fences just in case
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.lower().startswith("json"):
                text = text[4:]
            text = text.rsplit("```", 1)[0]
            text = text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            return ExtractionResult(None, latency, cost, raw, f"JSONDecodeError: {e}")

        # Auto-fill the archetype booleans if missing (defensive — they're derivable)
        if "codigo_painel" in data:
            derived = derive_archetype_booleans(data["codigo_painel"])
            for k, v in derived.items():
                data.setdefault(k, v)

        try:
            geom = PanelGeometry.model_validate(data)
        except Exception as e:
            return ExtractionResult(None, latency, cost, raw, f"ValidationError: {e}")

        return ExtractionResult(geom, latency, cost, raw, None)


# ---------- registry ----------
_REGISTRY: dict[str, Callable[[], Extractor]] = {}


def register(name: str):
    def deco(factory: Callable[[], Extractor]):
        _REGISTRY[name] = factory
        return factory
    return deco


def _ensure_loaded() -> None:
    """Import all provider modules so they self-register."""
    from .extractors import claude, gemini, ollama  # noqa: F401


def get_extractor(name: str) -> Extractor:
    _ensure_loaded()
    if name not in _REGISTRY:
        raise KeyError(f"Unknown extractor '{name}'. Available: {sorted(_REGISTRY)}")
    return _REGISTRY[name]()


def available_extractors() -> list[str]:
    _ensure_loaded()
    return sorted(_REGISTRY)
