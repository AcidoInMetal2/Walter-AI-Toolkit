"""
Almacenamiento local de credenciales (API keys / tokens).

Se guardan en un archivo JSON dentro del proyecto pero FUERA del
control de versión (ver .gitignore: config/secrets.local.json), para
no depender de variables de entorno del sistema (setx en cmd) ni
exponer tokens en el código o en el repositorio.
"""
import json
from pathlib import Path

from config.paths import CONFIG_DIR

SECRETS_FILE = CONFIG_DIR / "secrets.local.json"


def cargar_secrets() -> dict:
    if not SECRETS_FILE.exists():
        return {}
    try:
        return json.loads(SECRETS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def guardar_secrets(hf_token: str | None = None, gemini_api_key: str | None = None) -> None:
    """
    Actualiza solo los campos que se pasan (None = no tocar ese campo),
    preservando lo que ya estaba guardado.
    """
    actuales = cargar_secrets()

    if hf_token is not None:
        actuales["hf_token"] = hf_token
    if gemini_api_key is not None:
        actuales["gemini_api_key"] = gemini_api_key

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SECRETS_FILE.write_text(json.dumps(actuales, indent=2, ensure_ascii=False), encoding="utf-8")
