"""
Walter AI Toolkit - Configuración
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from config.secrets_store import cargar_secrets

_secrets = cargar_secrets()


@dataclass(slots=True)
class Settings:
    whisper_model: str = "medium"
    language: str = "es"
    overwrite_output: bool = False
    save_log: bool = True
    verbose: bool = True

    # Token de HuggingFace para modelos "gated" (ej: pyannote).
    # Prioridad: 1) config/secrets.local.json (vía pantalla de
    # configuración en la app), 2) variable de entorno HF_TOKEN.
    hf_token: str = field(
        default_factory=lambda: _secrets.get("hf_token") or os.environ.get("HF_TOKEN", "")
    )

    # API key de Gemini (Google AI Studio). Misma prioridad que arriba.
    gemini_api_key: str = field(
        default_factory=lambda: _secrets.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", "")
    )

    # El nombre de los modelos de Gemini cambia seguido (Google los va
    # renovando cada pocos meses). Si en algún momento este deja de
    # existir, actualizar acá alcanza.
    gemini_model: str = "gemini-3.6-flash"

    # Carpeta del vault de Obsidian donde se guardan las notas de clase
    # generadas por IA. No es un dato sensible (no es un token), así que
    # va directo acá; si en algún momento cambiás de carpeta, se edita
    # este valor nomás.
    obsidian_vault_dir: Path = field(
        default_factory=lambda: Path(r"E:\TRADER\AlphaPro\Notas IA")
    )

settings = Settings()
