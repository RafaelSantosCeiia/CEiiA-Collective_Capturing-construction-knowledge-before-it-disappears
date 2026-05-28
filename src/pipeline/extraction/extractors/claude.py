"""Claude API extractor — Sonnet 4.6 with PDF input."""
from __future__ import annotations

import base64
import os

from ..base import Extractor, register
from ..splitter import SubPanelChunk


# Sonnet 4.6 pricing (per 1M tokens) — Mar 2026
_INPUT_USD_PER_MTOK = 3.0
_OUTPUT_USD_PER_MTOK = 15.0


class ClaudeExtractor(Extractor):
    name = "claude"

    def __init__(self, model: str = "claude-sonnet-4-6"):
        self.model = model
        try:
            from anthropic import Anthropic
        except ImportError as e:
            raise RuntimeError(
                "anthropic SDK not installed. Run: pip install anthropic"
            ) from e
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set in environment."
            )
        self.client = Anthropic()

    def _call(self, chunk: SubPanelChunk, prompt: str, system: str) -> tuple[str, float | None]:
        pdf_b64 = base64.standard_b64encode(chunk.extract_pdf_bytes()).decode("ascii")
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_b64,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        text = "".join(b.text for b in resp.content if b.type == "text")
        usage = resp.usage
        cost = (
            usage.input_tokens * _INPUT_USD_PER_MTOK / 1e6
            + usage.output_tokens * _OUTPUT_USD_PER_MTOK / 1e6
        )
        return text, cost


@register("claude")
def _factory() -> ClaudeExtractor:
    return ClaudeExtractor()
