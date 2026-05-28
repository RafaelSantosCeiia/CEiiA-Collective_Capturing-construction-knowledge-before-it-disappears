"""Ollama local extractor — uses a vision model (qwen2.5vl, llava, …).

Ollama vision models don't ingest PDF directly, so we render each page to PNG
first via PyMuPDF.
"""
from __future__ import annotations

import base64
import os

from ..base import Extractor, register
from ..splitter import SubPanelChunk


class OllamaExtractor(Extractor):
    name = "ollama"

    def __init__(self, model: str | None = None, host: str | None = None):
        self.model = model or os.environ.get("OLLAMA_MODEL", "qwen2.5vl:7b")
        self.host = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        try:
            import ollama  # noqa: F401
        except ImportError as e:
            raise RuntimeError(
                "ollama SDK not installed. Run: pip install ollama"
            ) from e
        from ollama import Client
        self.client = Client(host=self.host)

    def _call(self, chunk: SubPanelChunk, prompt: str, system: str) -> tuple[str, float | None]:
        pngs = chunk.render_pages_to_png(dpi=120)
        images_b64 = [base64.b64encode(p).decode("ascii") for p in pngs]
        resp = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt, "images": images_b64},
            ],
            format="json",
            options={
                "temperature": 0.0,
                "num_ctx": 16384,
                "num_predict": 2048,
            },
        )
        text = resp["message"]["content"]
        return text, 0.0  # local model = free


@register("ollama")
def _factory() -> OllamaExtractor:
    return OllamaExtractor()
