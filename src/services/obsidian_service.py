"""
Servicio de guardado de notas en el vault de Obsidian.

Responsabilidad única: escribir un archivo .md en la carpeta del vault.
No sabe nada de transcripciones ni de IA, solo recibe texto y lo guarda.
"""
from datetime import datetime
from pathlib import Path

from config.settings import settings
from src.services.base_service import BaseService


class ObsidianService(BaseService):

    def initialize(self) -> None:
        settings.obsidian_vault_dir.mkdir(parents=True, exist_ok=True)

    def shutdown(self) -> None:
        pass

    def guardar_nota(self, nombre_base: str, contenido: str) -> Path:
        """
        Guarda `contenido` como un .md dentro del vault, con nombre
        `nombre_base.md`. Si ya existe un archivo con ese nombre y
        settings.overwrite_output es False, agrega un timestamp para
        no pisar la nota anterior.
        """
        settings.obsidian_vault_dir.mkdir(parents=True, exist_ok=True)

        destino = settings.obsidian_vault_dir / f"{nombre_base}.md"

        if destino.exists() and not settings.overwrite_output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            destino = settings.obsidian_vault_dir / f"{nombre_base}_{timestamp}.md"

        destino.write_text(contenido, encoding="utf-8")

        return destino
