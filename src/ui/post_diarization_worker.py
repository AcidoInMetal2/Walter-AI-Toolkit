"""
Worker que corre diarización + cruce con Whisper de forma independiente,
sobre una transcripción que YA existe (no vuelve a llamar a Whisper).

Útil cuando el usuario transcribió sin diarizar y después decide que sí
quiere separar por hablantes, sin tener que repetir todo el proceso de
Whisper desde cero.
"""
from PySide6.QtCore import QThread, Signal

from src.core.context import Context
from src.modules.diarizer import Diarizer
from src.modules.transcript_merger import TranscriptMerger
from src.services.audio_resolver import AudioResolver


class PostDiarizationWorker(QThread):

    lineaRecibida = Signal(str)
    finalizado = Signal(object)   # Context con diarization_segments + transcript final
    error = Signal(str)

    def __init__(self, audio_path: str, transcript_segments: list[dict], num_speakers: int | None = None):
        super().__init__()
        self.audio_path = audio_path
        self.transcript_segments = transcript_segments
        self.num_speakers = num_speakers
        self.resolver = AudioResolver()

    def run(self):
        audio_file = None
        es_temporal = False
        try:
            context = Context()
            context.on_transcript_line = self.lineaRecibida.emit
            context.transcript_segments = self.transcript_segments
            context.num_speakers = self.num_speakers

            audio_file, es_temporal = self.resolver.resolver(
                self.audio_path, on_line=context.on_transcript_line
            )
            context.audio_file = audio_file

            context = Diarizer().execute(context)
            context = TranscriptMerger().execute(context)

            self.finalizado.emit(context)

        except Exception as e:
            self.error.emit(str(e))

        finally:
            if es_temporal and audio_file and audio_file.exists():
                audio_file.unlink(missing_ok=True)
