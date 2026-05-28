"""Pydantic schema for the 21 geometry features extracted per ECOCIAF sub-panel.

Same contract for every extractor (Claude, Gemini, Ollama, ...). The model
trains on these 21 features + the join keys are kept for downstream merges
with `ecociaf_times_long.parquet`.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


SubpanelCode = Literal["PCT", "PCK", "PCL", "PS", "PL", "PG", "PP", "PT", "PVB"]


class PanelGeometry(BaseModel):
    """One row per ECOCIAF sub-panel.

    Field names match `training_clean.parquet` exactly so the join is a
    no-op merge on `panel_id`.
    """

    model_config = {"extra": "forbid"}

    # --- join keys (kept for downstream merge — not features) ---
    panel_id: str = Field(..., description="ex: PCT01K, PG02K")
    is_id: str = Field(..., description="ex: IS01A, IS02A")
    project_id: str = Field(..., description="ex: ECOCIAF01")
    drawing_revision: str = Field(..., description="ex: A, A.1, B")

    # --- estrutura metálica (Kit Perfis) ---
    largura_painel_mm: int = Field(..., ge=100, le=4000)
    altura_painel_mm: int = Field(..., ge=100, le=4000)
    profundidade_painel_mm: int = Field(..., ge=10, le=4000)
    largura_perfil_mm: int = Field(..., ge=30, le=100)
    espessura_perfil_mm: float = Field(..., ge=0.3, le=3.0)
    num_montantes: int = Field(..., ge=2, le=20)
    num_raias: int = Field(..., ge=1, le=20)
    comprimento_montante_mm: int = Field(..., ge=100, le=4000)
    comprimento_raia_mm: int = Field(..., ge=100, le=4000)
    num_furos_raia: int = Field(..., ge=0, le=30)

    # --- placagem (Kit Placas) ---
    num_placas_por_face: int = Field(..., ge=1, le=10)
    perimetro_placa_total_mm: int = Field(..., ge=200, le=80000,
        description="Σ 2(L+W) de TODAS as placas da face")
    perimetro_placa_maior_mm: int = Field(..., ge=200, le=20000,
        description="2(L+W) da placa dominante (a de maior área)")
    espessura_placa_mm: float = Field(..., ge=5.0, le=30.0)
    placagem_dupla: bool
    tem_entalhes: bool

    # --- arquétipo ---
    codigo_painel: SubpanelCode
    e_tecto: bool
    e_pavimento: bool
    e_porta: bool
    e_zona_humida: bool

    @field_validator("panel_id")
    @classmethod
    def _panel_id_upper(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("codigo_painel", mode="before")
    @classmethod
    def _code_normalize(cls, v: str) -> str:
        """Normalize many surface forms back to the 9 canonical codes:
        'PG02K' → 'PG', 'PCT01K' → 'PCT', 'PGK' → 'PG', 'PCTK' → 'PCT', etc.
        Accepts already-canonical codes ('PCK', 'PT', 'PVB') as-is.
        """
        if not isinstance(v, str):
            return v
        v = v.strip().upper()
        canonical = {"PCT", "PCK", "PCL", "PS", "PL", "PG", "PP", "PT", "PVB"}
        if v in canonical:
            return v
        # Otherwise, peel digits + K suffix (e.g. PG02K → PG, PCT01K → PCT)
        peeled = v.rstrip("K").rstrip("0123456789")
        return peeled if peeled in canonical else v


FEATURE_COLUMNS: tuple[str, ...] = (
    "largura_painel_mm",
    "altura_painel_mm",
    "profundidade_painel_mm",
    "largura_perfil_mm",
    "espessura_perfil_mm",
    "num_montantes",
    "num_raias",
    "comprimento_montante_mm",
    "comprimento_raia_mm",
    "num_furos_raia",
    "num_placas_por_face",
    "perimetro_placa_total_mm",
    "perimetro_placa_maior_mm",
    "espessura_placa_mm",
    "placagem_dupla",
    "tem_entalhes",
    "codigo_painel",
    "e_tecto",
    "e_pavimento",
    "e_porta",
    "e_zona_humida",
)


def derive_archetype_booleans(codigo_painel: str) -> dict[str, bool]:
    """Derive the 4 archetype booleans from `codigo_painel`.

    Useful when an extractor is lazy and only returns `codigo_painel`.
    """
    c = codigo_painel.strip().upper()
    return {
        "e_tecto": c == "PT",
        "e_pavimento": c == "PVB",
        "e_porta": c == "PP",
        "e_zona_humida": c in {"PCT", "PCK", "PCL"},
    }
