"""
Módulo TranscriptMerger: cruza el texto transcripto por Whisper
(con timestamps) con los turnos de habla detectados por el Diarizer,
y arma el transcript final con hablantes.

Responsabilidad única: no transcribe, no diariza. Solo combina lo que
ya está en el Context.
"""
from src.core.context import Context
from src.core.time_utils import formatear_tiempo

SPEAKER_DESCONOCIDO = "SPEAKER_DESCONOCIDO"


class TranscriptMerger:

    def execute(self, context: Context) -> Context:

        if not context.transcript_segments:
            return context

        if not context.diarization_segments:
            return context

        self._avisar(context, "[Info] Cruzando transcripción con hablantes detectados...")

        segmentos_con_speaker = [
            {
                **segmento,
                "speaker": self._hablante_dominante(segmento, context.diarization_segments),
            }
            for segmento in context.transcript_segments
        ]

        bloques = self._agrupar_por_hablante(segmentos_con_speaker)

        context.metadata["speaker_blocks"] = bloques
        context.transcript = self._formatear(bloques)

        cantidad_speakers = len({b["speaker"] for b in bloques})
        self._avisar(
            context,
            f"[Info] Transcript final armado con {cantidad_speakers} hablante(s) "
            f"en {len(bloques)} bloque(s).",
        )

        return context

    @staticmethod
    def _hablante_dominante(segmento_whisper: dict, turnos_diarizacion: list[dict]) -> str:
        inicio_w, fin_w = segmento_whisper["start"], segmento_whisper["end"]

        mejor_speaker = None
        mejor_solapamiento = 0.0

        for turno in turnos_diarizacion:
            solapamiento = min(fin_w, turno["end"]) - max(inicio_w, turno["start"])
            if solapamiento > mejor_solapamiento:
                mejor_solapamiento = solapamiento
                mejor_speaker = turno["speaker"]

        if mejor_speaker is not None:
            return mejor_speaker

        punto_medio = (inicio_w + fin_w) / 2
        turno_cercano = min(
            turnos_diarizacion,
            key=lambda t: min(abs(t["start"] - punto_medio), abs(t["end"] - punto_medio)),
            default=None,
        )
        return turno_cercano["speaker"] if turno_cercano else SPEAKER_DESCONOCIDO

    @staticmethod
    def _agrupar_por_hablante(segmentos_con_speaker: list[dict]) -> list[dict]:
        if not segmentos_con_speaker:
            return []

        bloques = []
        actual = {
            "speaker": segmentos_con_speaker[0]["speaker"],
            "start": segmentos_con_speaker[0]["start"],
            "end": segmentos_con_speaker[0]["end"],
            "text": segmentos_con_speaker[0]["text"],
        }

        for segmento in segmentos_con_speaker[1:]:
            if segmento["speaker"] == actual["speaker"]:
                actual["end"] = segmento["end"]
                actual["text"] += " " + segmento["text"]
            else:
                bloques.append(actual)
                actual = {
                    "speaker": segmento["speaker"],
                    "start": segmento["start"],
                    "end": segmento["end"],
                    "text": segmento["text"],
                }

        bloques.append(actual)
        return bloques

    @staticmethod
    def _formatear(bloques: list[dict]) -> str:
        return "\n\n".join(
            f"[{formatear_tiempo(b['start'])} - {formatear_tiempo(b['end'])}] "
            f"[{b['speaker']}] {b['text']}"
            for b in bloques
        )

    @staticmethod
    def _avisar(context: Context, mensaje: str):
        if context.on_transcript_line:
            context.on_transcript_line(mensaje)
