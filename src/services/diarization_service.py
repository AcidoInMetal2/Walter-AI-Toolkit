"""
Servicio de diarización de hablantes (pyannote.audio).

Responsabilidad única: dado un audio, devolver los turnos de habla
detectados con sus timestamps y una etiqueta de speaker genérica
(SPEAKER_00, SPEAKER_01, ...). No sabe nada de Whisper ni de texto.
"""
from pathlib import Path

from config.settings import settings
from src.services.base_service import BaseService

MODELO_DIARIZACION = "pyannote/speaker-diarization-community-1"


class DiarizationService(BaseService):

    def __init__(self):
        self._pipeline = None

    def initialize(self) -> None:
        """
        Carga el pipeline de pyannote. Se hace acá (no en __init__) porque
        es una carga pesada (descarga/instancia el modelo) y así el
        ServiceManager decide cuándo pagar ese costo.
        """
        import torch
        from pyannote.audio import Pipeline

        if not settings.hf_token:
            raise RuntimeError(
                "Falta HF_TOKEN. Necesitás un token de HuggingFace con acceso "
                f"aceptado a '{MODELO_DIARIZACION}', configurado en la app "
                "(botón 'Configurar API Keys') o como variable de entorno HF_TOKEN."
            )

        self._pipeline = Pipeline.from_pretrained(
            MODELO_DIARIZACION,
            token=settings.hf_token,
        )

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._pipeline.to(device)

    def shutdown(self) -> None:
        self._pipeline = None

    def diarize(
        self,
        audio_file,
        num_speakers: int | None = None,
        min_speakers: int | None = None,
        max_speakers: int | None = None,
    ) -> list[dict]:
        """
        Devuelve una lista de turnos de habla:
        [{"start": 0.0, "end": 3.2, "speaker": "SPEAKER_00"}, ...]
        ordenada por tiempo de inicio.
        """
        if self._pipeline is None:
            self.initialize()

        import time

        import numpy as np
        import soundfile as sf
        import torch

        ruta = Path(audio_file)

        # En Windows, un antivirus (ej: Malwarebytes) puede quedarse un
        # rato "revisando" un archivo recién escrito por FFmpeg,
        # bloqueándolo. Con archivos grandes puede tardar varios segundos,
        # así que le damos bastante margen antes de darnos por vencidos.
        for _ in range(20):
            if ruta.exists() and ruta.stat().st_size > 0:
                break
            time.sleep(0.5)

        # Reintentamos la lectura en sí también, por si el bloqueo ocurre
        # justo al momento de abrir el archivo (no solo de crearlo).
        datos = None
        ultimo_error = None
        for _ in range(10):
            try:
                datos, sample_rate = sf.read(str(ruta), dtype="float32", always_2d=True)
                break
            except Exception as e:
                ultimo_error = e
                time.sleep(1.0)

        if datos is None:
            raise RuntimeError(
                f"No se pudo leer el audio en '{ruta}' después de varios intentos "
                f"(puede estar bloqueado por un antivirus). Error original: {ultimo_error}"
            )

        # Leemos el audio con soundfile (libsndfile), que no depende de
        # FFmpeg ni de torchcodec, y lo convertimos al formato que pide
        # pyannote: tensor (canales, tiempo) + sample_rate.
        waveform = torch.from_numpy(np.ascontiguousarray(datos.T))
        audio_input = {"waveform": waveform, "sample_rate": sample_rate}

        kwargs = {}
        if num_speakers is not None:
            kwargs["num_speakers"] = num_speakers
        else:
            if min_speakers is not None:
                kwargs["min_speakers"] = min_speakers
            if max_speakers is not None:
                kwargs["max_speakers"] = max_speakers

        diarizacion = self._pipeline(audio_input, **kwargs)

        segmentos = []
        for turno, speaker in diarizacion.speaker_diarization:
            segmentos.append({
                "start": round(turno.start, 3),
                "end": round(turno.end, 3),
                "speaker": speaker,
            })

        segmentos.sort(key=lambda s: s["start"])
        return segmentos
