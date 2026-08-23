"""
Walter AI Toolkit - Carga de prompts para los servicios de LLM.

Los prompts viven como archivos de texto plano en prompts/, para poder
editarlos sin tocar código. Este módulo solo los carga y expone.
"""
from config.paths import PROMPTS_DIR

PROMPT_LIMPIEZA = "limpieza"
PROMPT_RESUMEN = "resumen"
PROMPT_ANALISIS = "analisis"
PROMPT_CLASE = "clase"


def cargar_prompt(nombre: str) -> str:
    """
    Lee el contenido de prompts/<nombre>.md.txt.
    Usar las constantes PROMPT_* de este módulo para evitar typos.
    """
    ruta = PROMPTS_DIR / f"{nombre}.md.txt"

    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el prompt: {ruta}")

    return ruta.read_text(encoding="utf-8")
