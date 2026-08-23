"""
Resuelve un archivo de entrada (audio o video) a un archivo de audio
listo para usar, extrayendo con FFmpeg UNA sola vez si hace falta.

Antes, tanto el Transcriber como la diarización posterior extraían el
audio de un video por separado (y encima el Transcriber lo borraba
apenas terminaba Whisper). Este módulo centraliza esa resolución para
que, dentro de una misma corrida, Whisper y pyannote compartan el
mismo archivo ya extraído en vez de procesar el video dos veces.
"""
from pathlib import Path
from typing import Callable

from config.paths import TEMP_DIR
from src.services.ffmpeg_service import FFmpegService

EXTENSIONES_VIDEO = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv'}


class AudioResolver:

    def __init__(self):
        self.ffmpeg_service = FFmpegService()

    def resolver(self, origen, on_line: Callable[[str], None] | None = None) -> tuple[Path, bool]:
        """
        Devuelve (ruta_audio, es_temporal).

        Si `origen` ya es un archivo de audio, lo devuelve tal cual
        (es_temporal=False, nunca se borra). Si es un video, lo extrae
        una vez a TEMP_DIR y devuelve esa ruta (es_temporal=True, quien
        llama es responsable de borrarlo cuando termine de usarlo).
        """
        origen = Path(origen)

        if origen.suffix.lower() not in EXTENSIONES_VIDEO:
            return origen, False

        if on_line:
            on_line(f"[Info] Detectado video ({origen.suffix}). Extrayendo audio con FFmpeg...")

        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        destino_wav = TEMP_DIR / (origen.stem + ".wav")
        audio_extraido = self.ffmpeg_service.extract_audio(origen, destino_wav)

        if on_line:
            on_line("[Info] Audio extraído correctamente.")

        return audio_extraido, True
