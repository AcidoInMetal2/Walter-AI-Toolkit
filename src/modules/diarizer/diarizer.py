"""
Módulo Diarizer: detecta "quién habla cuándo" en un audio.

Etapa 1 (esta): pura diarización, sin cruzar con texto de Whisper.
Solo llena context.diarization_segments con turnos de habla
(SPEAKER_00, SPEAKER_01, ...) y sus timestamps. El cruce con el
texto transcripto (para armar el transcript final con hablantes)
es un paso posterior y separado.
"""
from src.core.context import Context
from src.services.diarization_service import DiarizationService


class Diarizer:

    def __init__(self, diarization_service: DiarizationService | None = None):
        self.service = diarization_service or DiarizationService()

    def execute(self, context: Context) -> Context:

        if context.audio_file is None:
            raise ValueError("Context.audio_file vacío: no hay audio para diarizar.")

        self._avisar(context, "[Info] Iniciando diarización de hablantes...")

        context.diarization_segments = self.service.diarize(
            audio_file=context.audio_file,
            num_speakers=context.num_speakers,
            min_speakers=context.min_speakers,
            max_speakers=context.max_speakers,
        )

        cantidad = len({s["speaker"] for s in context.diarization_segments})
        self._avisar(
            context,
            f"[Info] Diarización finalizada: {cantidad} hablante(s), "
            f"{len(context.diarization_segments)} turno(s) detectado(s).",
        )

        return context

    @staticmethod
    def _avisar(context: Context, mensaje: str):
        if context.on_transcript_line:
            context.on_transcript_line(mensaje)
