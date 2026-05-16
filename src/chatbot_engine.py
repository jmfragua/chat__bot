"""
Motor del chatbot que orquesta FAQs, LLM y guardrails.
"""

from typing import Dict, List, Tuple, Optional
import os
from src.faq_loader import FAQLoader
from src.llm_handler import LLMHandler
from src.guardrails import GuardrailValidator, ResponseStatus
from src.web_search import ControlledWebSearch


class ChatbotEngine:
    """Orquesta la lógica completa del chatbot de FAQs."""

    def __init__(
        self,
        faq_loader: FAQLoader,
        llm_handler: LLMHandler,
        guardrail_validator: GuardrailValidator,
        confidence_threshold: float = 0.6
    ):
        """
        Inicializa el motor del chatbot.

        Args:
            faq_loader: Instancia de FAQLoader con FAQs cargadas
            llm_handler: Instancia de LLMHandler para OpenAI
            guardrail_validator: Instancia de GuardrailValidator
            confidence_threshold: Umbral de confianza para respuestas
        """
        self.faq_loader = faq_loader
        self.llm_handler = llm_handler
        self.validator = guardrail_validator
        self.confidence_threshold = confidence_threshold
        self.conversation_log = []

        # Inicializar búsqueda web (opcional)
        enable_web_search = os.getenv("ENABLE_WEB_SEARCH", "false").lower() == "true"
        self.web_search = ControlledWebSearch(enabled=enable_web_search)

        # Configurar system prompt
        system_prompt = self.llm_handler.get_system_prompt_for_faq_chatbot()
        self.llm_handler.set_system_prompt(system_prompt)

    def process_question(self, pregunta: str) -> Dict:
        """
        Procesa una pregunta del usuario y retorna respuesta completa.

        Args:
            pregunta: Pregunta del usuario

        Returns:
            Dict con respuesta, metadatos, y estado
        """
        # Validar pregunta
        es_valida, error_msg = self.validator.validate_question(pregunta)
        if not es_valida:
            result = {
                'exito': False,
                'respuesta': f"❌ {error_msg}",
                'categoria': None,
                'confianza': 0.0,
                'fuente': 'validacion',
                'is_error': True
            }
            self.conversation_log.append(result)
            return result

        # Detectar si está fuera de dominio
        if self.validator.detect_out_of_domain(pregunta):
            respuesta = self.validator.format_out_of_scope_response(
                self.faq_loader.get_categories()[:3]
            )
            result = {
                'exito': False,
                'respuesta': respuesta,
                'categoria': 'Fuera de Alcance',
                'confianza': 0.0,
                'fuente': 'guardrails',
                'is_error': False
            }
            self.conversation_log.append(result)
            return result

        # PRIORIZAR búsqueda web para palabras clave importantes
        # (salario mínimo, UVT, datos actualizados)
        palabras_clave_web = ['salario mínimo', 'uvt', 'smmlv']
        debe_priorizar_web = any(keyword in pregunta.lower() for keyword in palabras_clave_web)

        # Verificar si debe buscar en web
        debe_buscar_web, dominio = self.web_search.should_search_web(pregunta)

        # Si hay palabras clave o detecta trigger, intentar búsqueda web PRIMERO
        if (debe_buscar_web or debe_priorizar_web):
            # Intentar búsqueda web
            resultado_web = self.web_search.search(pregunta, dominio)

            if resultado_web.get('exito'):
                respuesta_web = self.web_search.format_search_result(resultado_web)
                result = {
                    'exito': True,
                    'respuesta': respuesta_web,
                    'categoria': 'Búsqueda Web',
                    'confianza': 0.9,
                    'fuente': 'web_search',
                    'is_error': False
                }
                self.conversation_log.append(result)
                return result
            # Si la búsqueda web falla, continúa a FAQs

        # Buscar FAQs relevantes
        faqs_relevantes = self.faq_loader.search_faqs(pregunta, top_k=5)

        if not faqs_relevantes or faqs_relevantes[0][1] == 0:
            # No hay FAQs relevantes y no se pudo buscar en web
            respuesta = self.validator.format_out_of_scope_response(
                self.faq_loader.get_categories()
            )
            result = {
                'exito': False,
                'respuesta': respuesta,
                'categoria': 'Fuera de Alcance',
                'confianza': 0.0,
                'fuente': 'no_encontrada',
                'is_error': False
            }
            self.conversation_log.append(result)
            return result

        # Construir contexto de FAQs para el LLM
        faq_context = self.llm_handler.build_faq_context(faqs_relevantes)

        # Generar respuesta con LLM
        respuesta_llm, llm_success = self.llm_handler.generate_response(
            pregunta,
            faq_context=faq_context
        )

        if not llm_success:
            result = {
                'exito': False,
                'respuesta': "❌ Error al procesar tu pregunta. Por favor intenta de nuevo.",
                'categoria': None,
                'confianza': 0.0,
                'fuente': 'llm_error',
                'is_error': True
            }
            self.conversation_log.append(result)
            return result

        # Validar respuesta
        categoria_top = faqs_relevantes[0][0]['categoria']
        status, validation_msg = self.validator.validate_response(respuesta_llm, categoria_top, pregunta)

        if status == ResponseStatus.SENSITIVE_DATA:
            result = {
                'exito': False,
                'respuesta': "⚠️ No puedo compartir esa información por motivos de privacidad.",
                'categoria': None,
                'confianza': 0.0,
                'fuente': 'validacion_sensible',
                'is_error': False
            }
            self.conversation_log.append(result)
            return result

        if status == ResponseStatus.INVALID_FORMAT:
            result = {
                'exito': False,
                'respuesta': "⚠️ No puedo procesar esa respuesta. Por favor intenta de nuevo.",
                'categoria': None,
                'confianza': 0.0,
                'fuente': 'validacion_formato',
                'is_error': False
            }
            self.conversation_log.append(result)
            return result

        # Formatear respuesta con referencia
        respuesta_final = self.validator.format_faq_response(respuesta_llm, categoria_top)

        # Verificar tono
        tono_ok, tono_msg = self.validator.get_tone_check(respuesta_final)

        # Calcular confianza mejorada
        faq_score = faqs_relevantes[0][1]
        confidence_score = self.validator.get_confidence_score(respuesta_final, categoria_match=True)
        confianza = (faq_score + confidence_score) / 2

        result = {
            'exito': True,
            'respuesta': respuesta_final,
            'categoria': categoria_top,
            'confianza': confianza,
            'fuente': 'faq',
            'is_error': False,
            'pregunta_original': pregunta
        }

        self.conversation_log.append(result)
        return result

    def get_conversation_history(self) -> List[Dict]:
        """Retorna el historial de la conversación."""
        return self.llm_handler.get_history()

    def reset_conversation(self) -> None:
        """Limpia el historial de conversación."""
        self.llm_handler.clear_history()
        self.conversation_log = []

    def get_statistics(self) -> Dict:
        """Retorna estadísticas de la conversación actual."""
        total_preguntas = len(self.conversation_log)
        preguntas_exitosas = sum(1 for log in self.conversation_log if log.get('exito'))
        errores = sum(1 for log in self.conversation_log if log.get('is_error'))

        categorias_usadas = {}
        for log in self.conversation_log:
            if log.get('categoria'):
                cat = log['categoria']
                categorias_usadas[cat] = categorias_usadas.get(cat, 0) + 1

        return {
            'total_preguntas': total_preguntas,
            'preguntas_exitosas': preguntas_exitosas,
            'tasa_exito': (preguntas_exitosas / total_preguntas * 100) if total_preguntas > 0 else 0,
            'errores': errores,
            'categorias_consultadas': categorias_usadas,
            'confianza_promedio': (
                sum(log.get('confianza', 0) for log in self.conversation_log) / total_preguntas
                if total_preguntas > 0 else 0
            )
        }

    def get_available_categories(self) -> List[str]:
        """Retorna categorías disponibles."""
        return self.faq_loader.get_categories()


if __name__ == "__main__":
    # Ejemplo de uso
    from src.faq_loader import FAQLoader
    from src.llm_handler import LLMHandler
    from src.guardrails import GuardrailValidator

    try:
        # Inicializar componentes
        loader = FAQLoader()
        llm = LLMHandler()
        validator = GuardrailValidator(loader.get_categories())

        # Crear chatbot
        chatbot = ChatbotEngine(loader, llm, validator)

        print("Chatbot Engine Inicializado")
        print("=" * 50)
        print(f"Categorías disponibles: {chatbot.get_available_categories()}")

        # Procesar pregunta de prueba
        print("\nProcesando pregunta de prueba...")
        resultado = chatbot.process_question("¿Cómo puedo recuperar mi usuario?")

        print(f"\nRespuesta: {resultado['respuesta']}")
        print(f"Categoría: {resultado['categoria']}")
        print(f"Confianza: {resultado['confianza']:.2f}")
        print(f"Éxito: {resultado['exito']}")

        # Mostrar estadísticas
        stats = chatbot.get_statistics()
        print(f"\n\nEstadísticas:")
        print(f"  Total preguntas: {stats['total_preguntas']}")
        print(f"  Tasa de éxito: {stats['tasa_exito']:.1f}%")

    except ValueError as e:
        print(f"Error: {e}")
        print("Asegúrate de configurar OPENAI_API_KEY")
