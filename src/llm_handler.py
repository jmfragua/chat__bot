"""
Módulo para integración con OpenAI API.
Gestiona la comunicación con el modelo y el contexto de la conversación.
"""

import os
from typing import List, Dict, Tuple, Optional
from openai import OpenAI, APIError


class LLMHandler:
    """Maneja la integración con OpenAI para procesamiento de lenguaje natural."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        max_history: int = 10,
        temperature: float = 0.3
    ):
        """
        Inicializa el manejador de OpenAI.

        Args:
            api_key: Clave de API de OpenAI (si no se proporciona, usa variable de entorno)
            model: Modelo a usar (gpt-4o-mini por defecto)
            max_history: Máximo número de mensajes en historial
            temperature: Temperatura para generación (0.3 = menos creativo, más determinista)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY no configurada. Configura la variable de entorno o pásala al constructor.")

        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.max_history = max_history
        self.temperature = temperature
        self.conversation_history = []

    def set_system_prompt(self, system_prompt: str) -> None:
        """
        Establece el prompt del sistema.

        Args:
            system_prompt: Instrucciones del sistema para el chatbot
        """
        self.system_prompt = system_prompt

    def add_to_history(self, role: str, content: str) -> None:
        """
        Añade un mensaje al historial de conversación.

        Args:
            role: "user" o "assistant"
            content: Contenido del mensaje
        """
        self.conversation_history.append({
            "role": role,
            "content": content
        })

        # Limitar historial a max_history mensajes
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

    def clear_history(self) -> None:
        """Limpia el historial de conversación."""
        self.conversation_history = []

    def get_history(self) -> List[Dict]:
        """Retorna el historial de conversación actual."""
        return self.conversation_history.copy()

    def generate_response(
        self,
        user_message: str,
        faq_context: str = "",
        max_tokens: int = 500
    ) -> Tuple[str, bool]:
        """
        Genera una respuesta usando OpenAI.

        Args:
            user_message: Mensaje del usuario
            faq_context: Contexto de FAQs relevantes para la respuesta
            max_tokens: Máximo número de tokens en la respuesta

        Returns:
            Tupla (respuesta, éxito)
        """
        # Añadir mensaje del usuario al historial
        self.add_to_history("user", user_message)

        try:
            # Preparar mensajes con contexto de FAQs si está disponible
            messages = [{"role": "system", "content": self.system_prompt}]

            # Añadir contexto de FAQs si está disponible
            if faq_context:
                messages.append({
                    "role": "system",
                    "content": f"Contexto de FAQs disponibles:\n{faq_context}"
                })

            # Añadir historial de conversación
            messages.extend(self.conversation_history)

            # Llamar a OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=max_tokens,
                top_p=0.9
            )

            # Extraer respuesta
            assistant_message = response.choices[0].message.content

            # Añadir respuesta al historial
            self.add_to_history("assistant", assistant_message)

            return assistant_message, True

        except APIError as e:
            error_msg = f"Error de API OpenAI: {str(e)}"
            print(f"⚠️ {error_msg}")
            return error_msg, False

    def get_system_prompt_for_faq_chatbot(self) -> str:
        """
        Retorna el prompt del sistema optimizado para chatbot de FAQs.

        Returns:
            System prompt listo para usar
        """
        return """Eres un asistente virtual especializado en temas de **Nómina y Contratación**.

Tu rol es:
1. Responder preguntas frecuentes basadas **únicamente** en las FAQs proporcionadas
2. Mantener un tono profesional, amable y respetuoso
3. Ser claro y conciso en tus respuestas

Reglas importantes:
- NUNCA inventes respuestas. Si una pregunta no está en las FAQs, debes informar que está "fuera de alcance"
- SIEMPRE cita la categoría de la respuesta con formato: [Fuente: FAQ 'Categoría']
- Si no encuentras respuesta, sugiere categorías relacionadas: General, Nómina y Pagos, Beneficios, Vacaciones y Licencias, Certificaciones, Contratación, Seguridad Social, Jornada y Modalidades
- No reveles datos sensibles, nombres de empresas, o información personal
- Si un usuario necesita contacto directo, sugiere comunicarse con el equipo de Nómina y Contratación

Responde siempre en español colombiano y usa un tono que inspire confianza."""

    @staticmethod
    def build_faq_context(faqs: List[Dict], top_k: int = 5) -> str:
        """
        Construye contexto de FAQs para pasar al LLM.

        Args:
            faqs: Lista de FAQs relevantes (tuplas de faq dict y score)
            top_k: Máximo de FAQs a incluir

        Returns:
            String formateado con FAQs
        """
        if not faqs:
            return ""

        context = "FAQs Relevantes:\n"
        for i, (faq, score) in enumerate(faqs[:top_k], 1):
            context += f"\n{i}. [{faq['categoria']}] P: {faq['pregunta']}\n   R: {faq['respuesta']}\n"

        return context


if __name__ == "__main__":
    # Ejemplo de uso
    try:
        handler = LLMHandler()
        system_prompt = handler.get_system_prompt_for_faq_chatbot()
        handler.set_system_prompt(system_prompt)

        # Simular conversación
        print("Prueba de LLM Handler con OpenAI")
        print("=" * 50)

        # Primera pregunta
        response1, success1 = handler.generate_response(
            "¿Hola, cómo estás?",
            faq_context="[Esta es una pregunta de prueba]"
        )
        print(f"\nUsuario: ¿Hola, cómo estás?")
        print(f"Bot: {response1}")
        print(f"Éxito: {success1}")

        # Segunda pregunta
        response2, success2 = handler.generate_response("¿Cuál es tu nombre?")
        print(f"\nUsuario: ¿Cuál es tu nombre?")
        print(f"Bot: {response2}")
        print(f"Éxito: {success2}")

        print(f"\n\nHistorial total: {len(handler.get_history())} mensajes")

    except ValueError as e:
        print(f"Error de configuración: {e}")
        print("Asegúrate de configurar OPENAI_API_KEY en tu .env")
