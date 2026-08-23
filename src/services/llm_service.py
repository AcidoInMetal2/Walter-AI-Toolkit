"""
Servicio de generación de texto vía Gemini (Google AI Studio).

Responsabilidad única: mandarle un prompt + texto a Gemini y devolver
la respuesta. No sabe nada de transcripciones, prompts específicos,
ni de Obsidian.
"""
from src.services.base_service import BaseService
from config.settings import settings


class LLMService(BaseService):

    def __init__(self):
        self._client = None

    def initialize(self) -> None:
        from google import genai

        if not settings.gemini_api_key:
            raise RuntimeError(
                "Falta GEMINI_API_KEY. Generá una en https://aistudio.google.com "
                "y configurala en la app (botón 'Configurar API Keys') o como "
                "variable de entorno GEMINI_API_KEY."
            )

        self._client = genai.Client(api_key=settings.gemini_api_key)

    def shutdown(self) -> None:
        self._client = None

    def generar(self, prompt: str, texto: str, modelo: str | None = None) -> str:
        """
        Manda prompt + texto a Gemini y devuelve la respuesta como string.
        `prompt` son las instrucciones (ej: "resumí lo siguiente...") y
        `texto` es el contenido sobre el que trabaja (la transcripción).
        """
        if self._client is None:
            self.initialize()

        contenido = f"{prompt}\n\n---\n\n{texto}"

        respuesta = self._client.models.generate_content(
            model=modelo or settings.gemini_model,
            contents=contenido,
        )

        return respuesta.text or ""
