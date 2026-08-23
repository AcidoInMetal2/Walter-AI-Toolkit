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
import json
import sys
from pathlib import Path

# Aseguramos que la raíz del proyecto esté en sys.path, sin importar
# desde qué directorio se invoque este script.
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.context import Context
from src.modules.diarizer import Diarizer

UMBRAL_TURNO_SOSPECHOSO = 0.3  # segundos: turnos más cortos que esto probablemente son ruido


def main():

    parser = argparse.ArgumentParser(description="Prueba standalone de diarización (pyannote).")
    parser.add_argument("audio", help="Ruta al archivo de audio corto a diarizar.")
    parser.add_argument("--speakers", type=int, default=None, help="Número exacto de hablantes (opcional).")
    parser.add_argument("--min-speakers", type=int, default=None, help="Mínimo de hablantes (opcional).")
    parser.add_argument("--max-speakers", type=int, default=None, help="Máximo de hablantes (opcional).")
    parser.add_argument("--muestra", type=int, default=15, help="Cuántos turnos mostrar en consola (default 15).")
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

    segmentos = context.diarization_segments

    # --- Guardamos el detalle completo en un archivo, para inspección libre ---
    salida = ROOT_DIR / "temp" / f"{audio_path.stem}_diarizacion.json"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(segmentos, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- Muestra acotada en consola ---
    print(f"\n=== Primeros {args.muestra} turnos ===\n")
    for segmento in segmentos[:args.muestra]:
        _imprimir_turno(segmento)

    if len(segmentos) > args.muestra:
        print(f"\n=== Últimos {min(args.muestra, 5)} turnos ===\n")
        for segmento in segmentos[-min(args.muestra, 5):]:
            _imprimir_turno(segmento)

    # --- Estadísticas para juzgar sobre-segmentación ---
    duraciones = [s["end"] - s["start"] for s in segmentos]
    cortos = [d for d in duraciones if d < UMBRAL_TURNO_SOSPECHOSO]

    tiempo_por_hablante = {}
    for s in segmentos:
        tiempo_por_hablante[s["speaker"]] = tiempo_por_hablante.get(s["speaker"], 0.0) + (s["end"] - s["start"])

    print("\n=== Estadísticas ===\n")
    print(f"Total de turnos: {len(segmentos)}")
    print(f"Duración promedio por turno: {sum(duraciones)/len(duraciones):.2f}s")
    print(f"Turnos menores a {UMBRAL_TURNO_SOSPECHOSO}s (posible ruido/sobre-segmentación): "
          f"{len(cortos)} ({100*len(cortos)/len(segmentos):.1f}%)")
    print("Tiempo total hablado por speaker:")
    for speaker, segundos in sorted(tiempo_por_hablante.items()):
        minutos = segundos / 60
        print(f"  {speaker}: {minutos:.1f} min")

    print(f"\nDetalle completo guardado en: {salida}")


def _imprimir_turno(segmento: dict):
    inicio = segmento["start"]
    fin = segmento["end"]
    hablante = segmento["speaker"]
    print(f"[{inicio:7.2f}s -> {fin:7.2f}s]  {hablante}")


if __name__ == "__main__":
    main()

