"""
Servicio de transcripción vía Whisper (CLI).
"""
from pathlib import Path
from typing import Callable
import json
import subprocess

from config.paths import TRANSCRIPTIONS_DIR


class WhisperService:

    def __init__(self, whisper_exe=r'C:\Whisper\venv\Scripts\whisper.exe'):
        self.whisper = Path(whisper_exe)

    def transcribe(
        self,
        audio_file,
        model: str = 'medium',
        language: str = 'Spanish',
        on_line: Callable[[str], None] | None = None,
        output_dir=None,
    ) -> str:
        """
        Ejecuta Whisper sobre el archivo de audio, emitiendo cada línea de
        salida (segmentos transcritos) a través de on_line a medida que
        el proceso las va generando, en vez de esperar a que termine todo.

        `output_dir`: carpeta donde Whisper guarda sus salidas (txt/json/
        srt/etc). Si no se especifica, usa TRANSCRIPTIONS_DIR (default).
        """
        destino = Path(output_dir) if output_dir else TRANSCRIPTIONS_DIR
        destino.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(self.whisper), str(audio_file),
            '--model', model,
            '--language', language,
            '--device', 'cuda',
            '--output_dir', str(destino),
        ]

        proceso = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
        )

        lineas_salida = []

        for linea in proceso.stdout:
            linea = linea.rstrip('\r\n')
            if not linea.strip():
                continue
            lineas_salida.append(linea)
            if on_line:
                on_line(linea)

        proceso.wait()

        if proceso.returncode != 0:
            detalle = '\n'.join(lineas_salida[-20:]) or 'Whisper finalizó con error.'
            raise RuntimeError(detalle)

        txt = destino / (Path(audio_file).stem + '.txt')
        return txt.read_text(encoding='utf-8') if txt.exists() else ''

    def leer_segmentos(self, audio_file, output_dir=None) -> list[dict]:
        """
        Lee el .json que Whisper ya deja guardado (--output_format default
        es "all", así que siempre está ahí) y devuelve los segmentos con
        timestamps: [{"start": 0.0, "end": 3.2, "text": "..."}, ...]

        Necesario para poder cruzar el texto con los turnos de la
        diarización (pyannote). `output_dir` debe ser el mismo que se usó
        al transcribir, para encontrar el .json en el lugar correcto.
        """
        destino = Path(output_dir) if output_dir else TRANSCRIPTIONS_DIR
        json_path = destino / (Path(audio_file).stem + '.json')

        if not json_path.exists():
            return []

        data = json.loads(json_path.read_text(encoding='utf-8'))

        return [
            {
                "start": round(s["start"], 3),
                "end": round(s["end"], 3),
                "text": s["text"].strip(),
            }
            for s in data.get("segments", [])
        ]
