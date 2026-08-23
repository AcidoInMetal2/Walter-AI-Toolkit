"""
Prueba independiente del Diarizer.

No toca la app ni la UI. Corre pyannote sobre un audio corto y
muestra los turnos de habla detectados (Speaker + timestamps),
para validar el backend de diarización antes de integrarlo con Whisper.

Uso:
    (venv) C:\\WalterAI> python scripts\\test_diarizer.py "ruta\\al\\audio_corto.wav"

    Opcional, si ya sabés cuántos hablantes hay:
    (venv) C:\\WalterAI> python scripts\\test_diarizer.py "audio_corto.wav" --speakers 2

Requiere la variable de entorno HF_TOKEN seteada con un token de
HuggingFace que tenga aceptados los términos de:
    https://huggingface.co/pyannote/speaker-diarization-community-1
"""
import argparse
import sys
from pathlib import Path

# Aseguramos que la raíz del proyecto esté en sys.path, sin importar
# desde qué directorio se invoque este script.
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.context import Context
from src.modules.diarizer import Diarizer


def main():

    parser = argparse.ArgumentParser(description="Prueba standalone de diarización (pyannote).")
    parser.add_argument("audio", help="Ruta al archivo de audio corto a diarizar.")
    parser.add_argument("--speakers", type=int, default=None, help="Número exacto de hablantes (opcional).")
    parser.add_argument("--min-speakers", type=int, default=None, help="Mínimo de hablantes (opcional).")
    parser.add_argument("--max-speakers", type=int, default=None, help="Máximo de hablantes (opcional).")
    args = parser.parse_args()

    audio_path = Path(args.audio)

    if not audio_path.exists():
        print(f"[ERROR] No se encontró el archivo: {audio_path}")
        sys.exit(1)

    context = Context()
    context.audio_file = audio_path
    context.num_speakers = args.speakers
    context.min_speakers = args.min_speakers
    context.max_speakers = args.max_speakers
    context.on_transcript_line = print  # las líneas de progreso van directo a consola

    print(f"\n=== Diarizando: {audio_path.name} ===\n")

    diarizer = Diarizer()
    context = diarizer.execute(context)

    print("\n=== Turnos detectados ===\n")
    for segmento in context.diarization_segments:
        inicio = segmento["start"]
        fin = segmento["end"]
        hablante = segmento["speaker"]
        print(f"[{inicio:7.2f}s -> {fin:7.2f}s]  {hablante}")

    print(f"\nTotal de turnos: {len(context.diarization_segments)}")


if __name__ == "__main__":
    main()
