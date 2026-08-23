"""
Worker que ejecuta la cadena de IA (limpieza -> resumen -> análisis ->
nota final) en un hilo aparte para no congelar la UI.
"""
from PySide6.QtCore import QThread, Signal

from src.core.context import Context
from src.modules.ai_reviewer import AIReviewer


class AIReviewWorker(QThread):

    lineaRecibida = Signal(str)
    finalizado = Signal(object)   # Context con los resultados en metadata
    error = Signal(str)

    def __init__(self, texto: str, saltear_limpieza: bool = False):
        super().__init__()
        self.texto = texto
        self.saltear_limpieza = saltear_limpieza

    def run(self):
        try:
            context = Context()
            context.transcript = self.texto
            context.on_transcript_line = self.lineaRecibida.emit

            reviewer = AIReviewer(saltear_limpieza=self.saltear_limpieza)
            context = reviewer.execute(context)

            self.finalizado.emit(context)

        except Exception as e:
            self.error.emit(str(e))
