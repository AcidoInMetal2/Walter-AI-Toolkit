"""
Módulo Transcriber: transcribe un audio ya resuelto (context.audio_file)
con Whisper. NO se encarga de detectar/extraer video — eso lo resuelve
AudioResolver antes de llegar acá, así el mismo audio extraído se puede
reutilizar también para la diarización sin procesar el video dos veces.
"""
from src.core.context import Context
from src.services.whisper_service import WhisperService


class Transcriber:
    def __init__(self):
        self.whisper_service = WhisperService()

    def execute(self, context: Context) -> Context:

        if context.audio_file is None:
            raise ValueError("Context.audio_file vacío: no hay audio para transcribir.")

        context.transcript = self.whisper_service.transcribe(
            audio_file=context.audio_file,
            model=context.metadata.get('model', 'medium'),
            language=context.language,
            on_line=context.on_transcript_line,
            output_dir=context.carpeta_transcripciones,
        )

        context.transcript_segments = self.whisper_service.leer_segmentos(
            context.audio_file,
            output_dir=context.carpeta_transcripciones,
        )

        return context
