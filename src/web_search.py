"""
Módulo opcional de búsqueda web para consultas sobre datos públicos.
Solo permite búsquedas en dominios permitidos (mintrabajo.gov.co, ugpp.gov.co, etc)
"""

import requests
from typing import Dict, List, Optional, Tuple
import re


class ControlledWebSearch:
    """Realiza búsquedas web controladas en dominios permitidos."""

    # Dominios permitidos para búsqueda
    ALLOWED_DOMAINS = {
        'mintrabajo.gov.co': {
            'nombre': 'Ministerio del Trabajo',
            'search_url': 'https://www.mintrabajo.gov.co/web/guest/search',
            'descripcion': 'Información laboral oficial de Colombia'
        },
        'ugpp.gov.co': {
            'nombre': 'Unidad de Gestión Pensional y Parafiscal',
            'search_url': 'https://www.ugpp.gov.co/',
            'descripcion': 'Información sobre pensiones y parafiscales'
        },
        'dane.gov.co': {
            'nombre': 'DANE - Departamento Administrativo Nacional de Estadística',
            'search_url': 'https://www.dane.gov.co/',
            'descripcion': 'Estadísticas oficiales de Colombia'
        }
    }

    # Palabras clave que disparan búsqueda web
    SEARCH_TRIGGERS = {
        'salario mínimo': 'mintrabajo.gov.co',
        'uvt': 'dane.gov.co',
        'smmlv': 'mintrabajo.gov.co',
        'pensión': 'ugpp.gov.co',
        'fondo de pensión': 'ugpp.gov.co',
        'fecha de pago': 'ugpp.gov.co'
    }

    def __init__(self, enabled: bool = False, timeout: int = 5):
        """
        Inicializa el buscador web.

        Args:
            enabled: Si la búsqueda web está habilitada
            timeout: Timeout para requests en segundos
        """
        self.enabled = enabled
        self.timeout = timeout
        self.search_history = []

    def should_search_web(self, pregunta: str) -> Tuple[bool, Optional[str]]:
        """
        Determina si una pregunta debe disparar búsqueda web.

        Args:
            pregunta: Pregunta del usuario

        Returns:
            Tupla (debe_buscar, dominio_sugerido)
        """
        if not self.enabled:
            return False, None

        pregunta_lower = pregunta.lower()

        for trigger, domain in self.SEARCH_TRIGGERS.items():
            if trigger in pregunta_lower:
                return True, domain

        return False, None

    def search(self, query: str, domain: str = None) -> Dict:
        """
        Realiza búsqueda web en dominio permitido.

        Args:
            query: Término de búsqueda
            domain: Dominio específico a buscar

        Returns:
            Dict con resultados de búsqueda
        """
        if not self.enabled:
            return {
                'exito': False,
                'error': 'Búsqueda web deshabilitada',
                'resultados': []
            }

        if domain and domain not in self.ALLOWED_DOMAINS:
            return {
                'exito': False,
                'error': f'Dominio no permitido: {domain}',
                'resultados': []
            }

        try:
            # Para esta demostración, retornamos un resultado simulado
            # En producción, esto implementaría scraping real
            resultado = self._simulate_search(query, domain)

            self.search_history.append({
                'query': query,
                'domain': domain,
                'resultado': resultado
            })

            return resultado

        except Exception as e:
            return {
                'exito': False,
                'error': f'Error en búsqueda: {str(e)}',
                'resultados': []
            }

    def _simulate_search(self, query: str, domain: Optional[str] = None) -> Dict:
        """
        Simula resultados de búsqueda (en producción sería scraping real).

        Args:
            query: Término de búsqueda
            domain: Dominio

        Returns:
            Resultados simulados
        """
        # Resultados simulados para demostración
        resultados_db = {
            'salario mínimo': [
                {
                    'titulo': 'Salario Mínimo 2024 Colombia',
                    'resumen': 'El salario mínimo en Colombia para 2024 es de $1,300,000 pesos mensuales.',
                    'url': 'https://www.mintrabajo.gov.co/salario-minimo',
                    'fuente': 'mintrabajo.gov.co'
                }
            ],
            'uvt': [
                {
                    'titulo': 'UVT 2024',
                    'resumen': 'La UVT (Unidad de Valor Tributario) para 2024 es de $46,045.',
                    'url': 'https://www.dane.gov.co/uvt',
                    'fuente': 'dane.gov.co'
                }
            ]
        }

        query_lower = query.lower()
        for trigger, results in resultados_db.items():
            if trigger in query_lower:
                return {
                    'exito': True,
                    'query': query,
                    'domain': domain,
                    'resultados': results,
                    'fuente': 'web_search'
                }

        return {
            'exito': False,
            'query': query,
            'error': 'No se encontraron resultados',
            'resultados': []
        }

    def format_search_result(self, resultado: Dict) -> str:
        """
        Formatea resultados de búsqueda para mostrar al usuario.

        Args:
            resultado: Resultado de búsqueda

        Returns:
            String formateado
        """
        if not resultado['exito']:
            return f"No se encontraron resultados para: {resultado['query']}"

        formatted = f"📌 Resultados de búsqueda para: {resultado['query']}\n\n"

        for i, res in enumerate(resultado['resultados'], 1):
            formatted += f"{i}. **{res['titulo']}**\n"
            formatted += f"   {res['resumen']}\n"
            formatted += f"   🔗 Fuente: {res['fuente']}\n\n"

        return formatted

    def get_allowed_domains_info(self) -> str:
        """Retorna información sobre dominios permitidos."""
        info = "**Dominios permitidos para búsqueda web:**\n\n"
        for domain, data in self.ALLOWED_DOMAINS.items():
            info += f"• **{data['nombre']}** ({domain})\n"
            info += f"  {data['descripcion']}\n\n"
        return info

    def get_search_history(self) -> List[Dict]:
        """Retorna historial de búsquedas realizadas."""
        return self.search_history.copy()


if __name__ == "__main__":
    # Ejemplo de uso
    searcher = ControlledWebSearch(enabled=True)

    print("Búsqueda Web Controlada")
    print("=" * 50)

    # Probar detección de triggers
    preguntas = [
        "¿Cuál es el salario mínimo en 2024?",
        "¿Qué es la UVT?",
        "¿Cómo funciona el chatbot?"
    ]

    for pregunta in preguntas:
        debe_buscar, domain = searcher.should_search_web(pregunta)
        print(f"\n'{pregunta}'")
        print(f"  Debe buscar web: {debe_buscar}")
        if debe_buscar:
            print(f"  Dominio: {domain}")

    # Realizar búsqueda
    print("\n\nBúsqueda de ejemplo:")
    resultado = searcher.search("salario mínimo", "mintrabajo.gov.co")
    print(searcher.format_search_result(resultado))
