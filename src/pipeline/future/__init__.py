"""Subsistema `future/` — visão de futuro com dados FICTÍCIOS.

Demonstra o que dados mais ricos desbloqueiam: 4 modelos sintéticos que
mostram padrões acionáveis (desperdício, temperatura, experiência, hora do dia).

NÃO toca no pipeline real — gera datasets próprios em `data/training/future/`,
treina modelos próprios e é servido por endpoints/página próprios. Reutiliza a
maquinaria honesta de avaliação de `pipeline.estimate` (piso de ruído, LOPO,
intervalos conformais), mas com uma design-matrix generalizada que aceita
features extra (temperatura, experiência, hora).
"""
from __future__ import annotations

from pathlib import Path

FUTURE_DIR = Path("data/training/future")

# Configuração dos 4 modelos: nome → coluna de feature extra (None = general).
MODELS: dict[str, str | None] = {
    "general": None,
    "temperature": "temperatura_c",
    "experience": "experiencia_meses",
    "timeofday": "hora_do_dia",
}

# Pseudo-micro-ops de desperdício (só no modelo general).
OP_IDLE = 15      # tempo inútil SEM valor (telemóvel, etc.) — aleatório
OP_MATERIAL = 16  # tempo inútil NECESSÁRIO (ir buscar material) — sistemático
