"""
Worker que ejecuta la transcripción (y opcionalmente diarización) en un
hilo aparte para no congelar la UI.

El audio se resuelve UNA sola vez con AudioResolver (si es video, se
extrae una única vez) y se comparte entre Transcriber y Diarizer — así
no se procesa el mismo video dos veces. Solo se borra al final, cuando
ya no lo necesita ninguno de los dos pasos.
"""
from PySide6.QtCore import QThread, Signal

from src.core.context import Context
from src.core.pipeline import Pipeline
from src.modules.transcriber import Transcriber
from src.modules.diarizer import Diarizer
from src.modules.transcript_merger import TranscriptMerger
from src.services.audio_resolver import AudioResolver


class TranscriptionWorker(QThread):

    lineaRecibida = Signal(str)
    finalizado = Signal(object)   # Context con el resultado
    error = Signal(str)

    def __init__(
        self,
        audio_path: str,
        modelo: str = "medium",
        idioma: str = "Spanish",
        diarizar: bool = False,
        num_speakers: int | None = None,
        carpeta_transcripciones=None,
    ):
        super().__init__()
        self.audio_path = audio_path
        self.modelo = modelo
        self.idioma = idioma
        self.diarizar = diarizar
        self.num_speakers = num_speakers
        self.carpeta_transcripciones = carpeta_transcripciones
        self.resolver = AudioResolver()

    def run(self):
        audio_file = None
        es_temporal = False
        try:
            context = Context()
            context.language = self.idioma
            context.metadata["model"] = self.modelo
            context.num_speakers = self.num_speakers
            context.carpeta_transcripciones = self.carpeta_transcripciones
            # Cada línea de progreso se reenvía como señal Qt, así se
            # actualiza la UI en vivo sin bloquear el hilo principal.
            context.on_transcript_line = self.lineaRecibida.emit

            audio_file, es_temporal = self.resolver.resolver(
                self.audio_path, on_line=context.on_transcript_line
            )
            context.audio_file = audio_file

            pipeline = Pipeline()
            pipeline.register(Transcriber())

            if self.diarizar:
                pipeline.register(Diarizer())
                pipeline.register(TranscriptMerger())

            context = pipeline.execute(context)

            self.finalizado.emit(context)

        except Exception as e:
            self.error.emit(str(e))

        finally:
            # El audio extraído (si el original era video) recién se
            # borra acá, después de que TODO el pipeline terminó de
            # usarlo (transcripción y, si corrió, diarización también).
            if es_temporal and audio_file and audio_file.exists():
                audio_file.unlink(missing_ok=True)
