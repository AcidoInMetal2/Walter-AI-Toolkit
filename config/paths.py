"""
Walter AI Toolkit - Rutas del proyecto
"""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

ASSETS_DIR = ROOT_DIR / "assets"
CONFIG_DIR = ROOT_DIR / "config"
DOCS_DIR = ROOT_DIR / "docs"
LOGS_DIR = ROOT_DIR / "logs"
MODELS_DIR = ROOT_DIR / "models"
OUTPUT_DIR = ROOT_DIR / "output"
PROMPTS_DIR = ROOT_DIR / "prompts"
SCRIPTS_DIR = ROOT_DIR / "scripts"
SRC_DIR = ROOT_DIR / "src"
TEMP_DIR = ROOT_DIR / "temp"

TRANSCRIPTIONS_DIR = OUTPUT_DIR / "transcripciones"

def create_directories():
    for d in (LOGS_DIR, OUTPUT_DIR, TEMP_DIR, TRANSCRIPTIONS_DIR):
        d.mkdir(parents=True, exist_ok=True)
