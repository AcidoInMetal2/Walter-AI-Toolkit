"""
Módulo AIReviewer: corre la cadena limpieza -> resumen -> análisis ->
nota final sobre un transcript, usando Gemini (LLMService).
"""
from config.prompts import (
    cargar_prompt,
    PROMPT_LIMPIEZA,
    PROMPT_RESUMEN,
    PROMPT_ANALISIS,
    PROMPT_CLASE,
)
from src.core.context import Context
from src.services.llm_service import LLMService


class AIReviewer:

    def __init__(self, llm_service: LLMService | None = None, saltear_limpieza: bool = False):
        self.llm_service = llm_service or LLMService()
        self.saltear_limpieza = saltear_limpieza

    def execute(self, context: Context) -> Context:

        if not context.transcript or not context.transcript.strip():
            raise ValueError("No hay transcript en el Context para analizar.")

        if self.saltear_limpieza:
            texto_limpio = context.transcript
        else:
            self._avisar(context, "[IA] Paso 1/4: Limpieza...")
            texto_limpio = self.llm_service.generar(cargar_prompt(PROMPT_LIMPIEZA), context.transcript)

        self._avisar(context, "[IA] Paso 2/4: Resumen...")
        resumen = self.llm_service.generar(cargar_prompt(PROMPT_RESUMEN), texto_limpio)

        self._avisar(context, "[IA] Paso 3/4: Análisis...")
        analisis = self.llm_service.generar(cargar_prompt(PROMPT_ANALISIS), texto_limpio)

        self._avisar(context, "[IA] Paso 4/4: Nota final de clase...")
        entrada_nota = f"## RESUMEN\n\n{resumen}\n\n## ANÁLISIS\n\n{analisis}"
        nota_final = self.llm_service.generar(cargar_prompt(PROMPT_CLASE), entrada_nota)

        context.metadata["texto_limpio"] = texto_limpio
        context.metadata["resumen"] = resumen
        context.metadata["analisis"] = analisis
        context.metadata["nota_final"] = nota_final

        self._avisar(context, "[IA] Análisis finalizado.")

        return context

    @staticmethod
    def _avisar(context: Context, mensaje: str):
        if context.on_transcript_line:
            context.on_transcript_line(mensaje)
