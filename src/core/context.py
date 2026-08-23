from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

@dataclass(slots=True)
class Context:
    input_file: Path|None=None
    audio_file: Path|None=None
    transcript: str=""
    language: str="es"
    metadata: dict[str,Any]=field(default_factory=dict)
    results: dict[str,Any]=field(default_factory=dict)
    services: dict[str,Any]=field(default_factory=dict)
    errors: list[str]=field(default_factory=list)
    on_transcript_line: Callable[[str], None]|None=None

    # --- Diarización ---
    diarization_segments: list[dict]=field(default_factory=list)  # [{start,end,speaker}, ...]
    num_speakers: int|None=None
    min_speakers: int|None=None
    max_speakers: int|None=None

    # --- Segmentos de Whisper con timestamps (para cruzar con diarización) ---
    transcript_segments: list[dict]=field(default_factory=list)  # [{start,end,text}, ...]

    # Carpeta de destino elegida por el usuario para los archivos de
    # transcripción (Whisper txt/json/etc + con_hablantes.txt). Si es
    # None, cada servicio usa su carpeta default (TRANSCRIPTIONS_DIR).
    carpeta_transcripciones: Path|None=None
