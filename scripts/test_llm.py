"""
Prueba independiente de la cadena LLM: limpieza -> resumen -> análisis -> nota final.

No toca la app ni la UI. Corre los 4 prompts contra Gemini sobre un
transcript ya generado (ideal: el "_con_hablantes.txt" que guarda la
app), para validar el motor LLM y los prompts antes de integrarlos
al pipeline principal.

Uso:
    (venv) C:\\WalterAI> python scripts\\test_llm.py "ruta\\al\\transcript.txt"

Requiere la variable de entorno GEMINI_API_KEY seteada
(generá una en https://aistudio.google.com).
"""
import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.paths import TEMP_DIR
from config.prompts import (
    cargar_prompt,
    PROMPT_LIMPIEZA,
    PROMPT_RESUMEN,
    PROMPT_ANALISIS,
    PROMPT_CLASE,
)
from src.services.llm_service import LLMService


def main():

    parser = argparse.ArgumentParser(description="Prueba standalone de la cadena LLM (Gemini).")
    parser.add_argument("transcript", help="Ruta al archivo .txt con la transcripción a procesar.")
    parser.add_argument(
        "--saltear-limpieza",
        action="store_true",
        help="Usar el transcript tal cual, sin pasar por el paso de limpieza (más rápido para probar).",
    )
    args = parser.parse_args()

    ruta_transcript = Path(args.transcript)

    if not ruta_transcript.exists():
        print(f"[ERROR] No se encontró el archivo: {ruta_transcript}")
        sys.exit(1)

    texto_original = ruta_transcript.read_text(encoding="utf-8")

    print(f"\n=== Procesando: {ruta_transcript.name} ({len(texto_original)} caracteres) ===\n")

    servicio = LLMService()

    if args.saltear_limpieza:
        print("[Info] Saltando limpieza (--saltear-limpieza).")
        texto_limpio = texto_original
    else:
        print("[Info] Paso 1/4: Limpieza...")
        texto_limpio = servicio.generar(cargar_prompt(PROMPT_LIMPIEZA), texto_original)
        print(f"  -> {len(texto_limpio)} caracteres.")

    print("[Info] Paso 2/4: Resumen...")
    resumen = servicio.generar(cargar_prompt(PROMPT_RESUMEN), texto_limpio)
    print(f"  -> {len(resumen)} caracteres.")

    print("[Info] Paso 3/4: Análisis...")
    analisis = servicio.generar(cargar_prompt(PROMPT_ANALISIS), texto_limpio)
    print(f"  -> {len(analisis)} caracteres.")

    print("[Info] Paso 4/4: Nota final de clase...")
    entrada_nota = f"## RESUMEN\n\n{resumen}\n\n## ANÁLISIS\n\n{analisis}"
    nota_final = servicio.generar(cargar_prompt(PROMPT_CLASE), entrada_nota)
    print(f"  -> {len(nota_final)} caracteres.")

    print("\n" + "=" * 60)
    print("NOTA FINAL")
    print("=" * 60 + "\n")
    print(nota_final)

    # Guardamos todo el detalle (cada paso por separado) para inspección.
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    salida = TEMP_DIR / f"{ruta_transcript.stem}_llm_test.md"

    contenido = (
        f"# Prueba LLM: {ruta_transcript.name}\n\n"
        f"## 1. Texto limpio\n\n{texto_limpio}\n\n"
        f"## 2. Resumen\n\n{resumen}\n\n"
        f"## 3. Análisis\n\n{analisis}\n\n"
        f"## 4. Nota final\n\n{nota_final}\n"
    )
    salida.write_text(contenido, encoding="utf-8")

    print(f"\nDetalle completo (los 4 pasos) guardado en: {salida}")


if __name__ == "__main__":
    main()
