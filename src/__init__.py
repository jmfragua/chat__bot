"""
Chatbot de FAQs para Nómina y Contratación
Asistente virtual informativo para consultas frecuentes
"""

__version__ = "1.0.0"
__author__ = "Equipo de Desarrollo"

from src.faq_loader import FAQLoader
from src.chatbot_engine import ChatbotEngine
from src.guardrails import GuardrailValidator
from src.llm_handler import LLMHandler

__all__ = [
    "FAQLoader",
    "ChatbotEngine",
    "GuardrailValidator",
    "LLMHandler"
]
