"""
Módulo de guardrails y validaciones para el chatbot.
Asegura que las respuestas sean confiables, apropiadas y dentro del dominio.
"""

import re
from typing import Dict, Tuple, List
from enum import Enum


class ResponseStatus(Enum):
    """Estados posibles de una respuesta."""
    VALID = "válida"
    OUT_OF_SCOPE = "fuera_de_alcance"
    SENSITIVE_DATA = "datos_sensibles"
    INVALID_FORMAT = "formato_inválido"


class GuardrailValidator:
    """Valida respuestas y preguntas contra guardrails de seguridad y dominio."""

    # Palabras clave fuera del dominio
    OUT_OF_DOMAIN_KEYWORDS = [
        'política', 'religión', 'personal', 'privado', 'secreto',
        'delito', 'fraude', 'criminal', 'ley penal', 'crimen',
        'receta', 'medicina', 'enfermedad', 'diagnóstico', 'tratamiento',
        'psicología', 'terapia'
    ]

    # Patrones de datos sensibles a detectar
    SENSITIVE_PATTERNS = {
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'phone': r'\+?[\d\s\-()]{10,}',
        'cc': r'\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}',  # Número de tarjeta
        'account': r'cuenta\s*[:\-]?\s*\d+',
        'salary': r'salario|sueldo\s*[:\-]?\s*[\$\d.,]+'
    }

    def __init__(self, categorias_disponibles: List[str]):
        """
        Inicializa el validador.

        Args:
            categorias_disponibles: Lista de categorías válidas de FAQs
        """
        self.categorias_disponibles = categorias_disponibles
        self.max_pregunta_length = 500
        self.min_pregunta_length = 3

    def validate_question(self, pregunta: str) -> Tuple[bool, str]:
        """
        Valida una pregunta del usuario.

        Args:
            pregunta: La pregunta a validar

        Returns:
            Tupla (es_válida, mensaje_error)
        """
        pregunta = pregunta.strip()

        # Validar longitud
        if len(pregunta) < self.min_pregunta_length:
            return False, "Pregunta muy corta. Por favor, sé más específico."

        if len(pregunta) > self.max_pregunta_length:
            return False, f"Pregunta muy larga (máximo {self.max_pregunta_length} caracteres)."

        # Validar que no esté vacía después de limpiar
        if not pregunta.replace('?', '').replace('¿', '').strip():
            return False, "Pregunta no válida. Por favor intenta de nuevo."

        return True, ""

    def detect_out_of_domain(self, pregunta: str) -> bool:
        """
        Detecta si una pregunta está fuera del dominio de nómina/contratación.

        Args:
            pregunta: La pregunta a evaluar

        Returns:
            True si está fuera de dominio, False si está dentro
        """
        pregunta_lower = pregunta.lower()

        for keyword in self.OUT_OF_DOMAIN_KEYWORDS:
            if keyword in pregunta_lower:
                return True

        return False

    def detect_sensitive_data(self, texto: str) -> Tuple[bool, List[str]]:
        """
        Detecta si el texto contiene datos sensibles.

        Args:
            texto: El texto a analizar

        Returns:
            Tupla (contiene_sensibles, tipos_encontrados)
        """
        tipos_encontrados = []

        for data_type, pattern in self.SENSITIVE_PATTERNS.items():
            if re.search(pattern, texto, re.IGNORECASE):
                tipos_encontrados.append(data_type)

        return len(tipos_encontrados) > 0, tipos_encontrados

    def validate_response(self, respuesta: str, categoria: str = None) -> Tuple[ResponseStatus, str]:
        """
        Valida una respuesta del chatbot.

        Args:
            respuesta: La respuesta a validar
            categoria: Categoría de la FAQ de donde viene la respuesta

        Returns:
            Tupla (estado, mensaje_detalle)
        """
        # Validar formato básico
        if not respuesta or not isinstance(respuesta, str):
            return ResponseStatus.INVALID_FORMAT, "Respuesta con formato inválido."

        respuesta = respuesta.strip()

        if len(respuesta) < 10:
            return ResponseStatus.INVALID_FORMAT, "Respuesta muy corta."

        # Detectar datos sensibles
        tiene_sensibles, tipos = self.detect_sensitive_data(respuesta)
        if tiene_sensibles:
            return ResponseStatus.SENSITIVE_DATA, f"Datos sensibles detectados: {', '.join(tipos)}"

        # Validar que tenga referencia a categoría
        if categoria and f"[Fuente:" not in respuesta:
            # Si la respuesta no tiene referencia a categoría, es potencialmente un problema
            # pero lo permitimos para respuestas que informan que está fuera de alcance
            pass

        return ResponseStatus.VALID, "Respuesta válida."

    def format_faq_response(self, respuesta: str, categoria: str) -> str:
        """
        Formatea una respuesta de FAQ con referencia a categoría.

        Args:
            respuesta: La respuesta de la FAQ
            categoria: Categoría de la FAQ

        Returns:
            Respuesta formateada con referencia
        """
        if "[Fuente:" not in respuesta:
            return f"[Fuente: FAQ '{categoria}']\n{respuesta}"
        return respuesta

    def format_out_of_scope_response(self, categorias_relacionadas: List[str] = None) -> str:
        """
        Crea una respuesta estándar para preguntas fuera de alcance.

        Args:
            categorias_relacionadas: Categorías que podrían ser relevantes

        Returns:
            Respuesta formateada
        """
        response = (
            "Lo siento, esa pregunta está fuera de mi alcance. "
            "Soy un asistente especializado en temas de **nómina y contratación**.\n\n"
        )

        if categorias_relacionadas:
            response += "**Categorías disponibles que podrían ayudarte:**\n"
            for cat in categorias_relacionadas:
                response += f"• {cat}\n"
            response += (
                "\nPor favor, reformula tu pregunta sobre alguno de estos temas, "
                "o contacta al equipo de Nómina y Contratación en caso de necesidad urgente."
            )
        else:
            response += (
                "Puedo ayudarte con preguntas sobre:\n"
                "• Nómina y Pagos\n"
                "• Beneficios\n"
                "• Vacaciones y Licencias\n"
                "• Certificaciones\n"
                "• Contratación\n"
                "• Seguridad Social\n"
                "• Jornada y Modalidades\n\n"
                "¿Tienes una pregunta sobre alguno de estos temas?"
            )

        return response

    def get_tone_check(self, respuesta: str) -> Tuple[bool, str]:
        """
        Verifica que el tono de la respuesta sea apropiado.

        Args:
            respuesta: La respuesta a evaluar

        Returns:
            Tupla (tono_apropiado, mensaje)
        """
        # Detectar lenguaje inapropiado (simplificado)
        offensive_words = ['idiota', 'estúpido', 'tonto', 'malo', 'problema']

        respuesta_lower = respuesta.lower()
        found_offensive = [word for word in offensive_words if word in respuesta_lower]

        if found_offensive:
            return False, f"Lenguaje inapropiado detectado: {', '.join(found_offensive)}"

        return True, "Tono apropiado"

    def extract_category_from_response(self, respuesta: str) -> str:
        """
        Extrae la categoría de referencia de una respuesta formateada.

        Args:
            respuesta: Respuesta con formato de categoría

        Returns:
            Nombre de la categoría o vacío si no se encuentra
        """
        match = re.search(r"\[Fuente:\s*FAQ\s*'([^']+)'\]", respuesta)
        if match:
            return match.group(1)
        return ""


if __name__ == "__main__":
    # Ejemplo de uso
    categorias = [
        "General", "Nómina y Pagos", "Beneficios",
        "Vacaciones y Licencias", "Certificaciones",
        "Contratación", "Seguridad Social", "Jornada y Modalidades"
    ]

    validator = GuardrailValidator(categorias)

    # Probar validación de pregunta
    print("Validación de preguntas:")
    preguntas_test = [
        "¿Cómo recupero mi usuario?",
        "x",
        "¿Cuál es la receta para hacer tamales?"
    ]

    for p in preguntas_test:
        es_valida, msg = validator.validate_question(p)
        print(f"  '{p}' → {es_valida} {msg if msg else ''}")

    # Probar detección de datos sensibles
    print("\n\nDetección de datos sensibles:")
    textos_test = [
        "El salario es $3000 pesos",
        "Mi usuario es juan@empresa.com"
    ]

    for t in textos_test:
        tiene, tipos = validator.detect_sensitive_data(t)
        print(f"  '{t}' → {tipos if tiene else 'Sin datos sensibles'}")
