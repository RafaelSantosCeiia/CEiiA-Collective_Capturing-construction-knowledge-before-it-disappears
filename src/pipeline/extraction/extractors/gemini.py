"""Gemini API extractor — Flash 3.5 with PDF input (free tier)."""
from __future__ import annotations

import os
import time as _time

from ..base import Extractor, register
from ..splitter import SubPanelChunk


# Gemini Flash pricing — Mar 2026 (free tier rates available)
_INPUT_USD_PER_MTOK = 0.075
_OUTPUT_USD_PER_MTOK = 0.30

# Free tier: ~10 RPM. Sleep between calls to stay under it.
_FREE_TIER_DELAY_SEC = 7.0
# Retry params for 429
_MAX_RETRIES = 4
_BACKOFF_BASE_SEC = 30.0


class GeminiExtractor(Extractor):
    name = "gemini"

    def __init__(self, model: str = "gemini-3.5-flash"):
        self.model = model
        try:
            from google import genai  # noqa: F401
        except ImportError as e:
            raise RuntimeError(
                "google-genai SDK not installed. Run: pip install google-genai"
            ) from e
        if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
            raise RuntimeError(
                "GEMINI_API_KEY (or GOOGLE_API_KEY) not set in environment."
            )
        from google import genai
        self.client = genai.Client()

    def _call(self, chunk: SubPanelChunk, prompt: str, system: str) -> tuple[str, float | None]:
        from google.genai import types
        from google.genai import errors as genai_errors

        pdf_bytes = chunk.extract_pdf_bytes()
        contents = [
            types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
            prompt,
        ]
        # Disable thinking on 2.5/3.x models to keep output budget for the JSON.
        thinking_cfg = (
            types.ThinkingConfig(thinking_budget=0)
            if any(t in self.model for t in ("2.5", "3.5", "3.0"))
            else None
        )

        last_err: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system,
                        response_mime_type="application/json",
                        max_output_tokens=8192,
                        temperature=0.0,
                        thinking_config=thinking_cfg,
                    ),
                )
                text = resp.text or ""
                cost = None
                if getattr(resp, "usage_metadata", None):
                    um = resp.usage_metadata
                    cost = (
                        (um.prompt_token_count or 0) * _INPUT_USD_PER_MTOK / 1e6
                        + (um.candidates_token_count or 0) * _OUTPUT_USD_PER_MTOK / 1e6
                    )
                _time.sleep(_FREE_TIER_DELAY_SEC)
                return text, cost
            except genai_errors.ClientError as e:
                last_err = e
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    wait = _BACKOFF_BASE_SEC * (2 ** attempt)
                    _time.sleep(wait)
                    continue
                raise
        raise last_err  # pyright: ignore


@register("gemini")
def _factory() -> GeminiExtractor:
    return GeminiExtractor()
