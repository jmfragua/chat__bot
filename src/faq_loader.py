"""
Módulo para cargar y procesar FAQs desde archivo Excel
"""

import pandas as pd
import json
import re
from typing import Dict, List, Tuple
from pathlib import Path


class FAQLoader:
    """Carga y procesa FAQs desde archivo Excel en una estructura accesible."""

    def __init__(self, excel_path: str = "FAQ_Chatbot_Nomina.xlsx"):
        """
        Inicializa el loader.

        Args:
            excel_path: Ruta al archivo Excel de FAQs
        """
        self.excel_path = Path(excel_path)
        self.faqs_by_category = {}
        self.all_faqs_flat = []
        self.faq_index = {}
        self.load_faqs()

    def load_faqs(self) -> None:
        """Carga las FAQs desde JSON (preferente) o desde Excel."""
        json_path = Path("faqs.json")

        # Intentar cargar desde JSON primero
        if json_path.exists():
            self._load_from_json(json_path)
        elif self.excel_path.exists():
            self._load_from_excel()
        else:
            raise FileNotFoundError(f"No se encontró {json_path} ni {self.excel_path}")

    def _load_from_json(self, json_path: Path) -> None:
        """Carga FAQs desde archivo JSON."""
        with open(json_path, 'r', encoding='utf-8') as f:
            faqs_data = json.load(f)

        faq_id = 1
        for item in faqs_data:
            categoria = item.get('categoria', 'General')
            pregunta = item.get('pregunta', '').strip()
            respuesta = item.get('respuesta', '').strip()

            if not pregunta or not respuesta:
                continue

            faq = {
                'id': faq_id,
                'pregunta': pregunta,
                'respuesta': respuesta,
                'categoria': categoria,
                'palabras_clave': self._extract_keywords(pregunta)
            }

            faq_id += 1
            self.all_faqs_flat.append(faq)
            self.faq_index[faq['id']] = faq

            if categoria not in self.faqs_by_category:
                self.faqs_by_category[categoria] = []
            self.faqs_by_category[categoria].append(faq)

    def _load_from_excel(self) -> None:
        """Carga FAQs desde Excel (fallback)."""
        df = pd.read_excel(self.excel_path)

        # Validar columnas requeridas
        required_columns = ['Segmento/categoria de pregunta', 'pregunta', 'respuesta']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Columnas requeridas no encontradas. Se esperan: {required_columns}")

        # Limpiar datos
        df = df.dropna(subset=['pregunta', 'respuesta'])
        df['pregunta'] = df['pregunta'].str.strip()
        df['respuesta'] = df['respuesta'].str.strip()
        df['Segmento/categoria de pregunta'] = df['Segmento/categoria de pregunta'].str.strip()

        # Agrupar por categoría
        for categoria, grupo in df.groupby('Segmento/categoria de pregunta'):
            faqs = []
            for idx, row in grupo.iterrows():
                faq = {
                    'id': len(self.all_faqs_flat) + 1,
                    'pregunta': row['pregunta'],
                    'respuesta': row['respuesta'],
                    'categoria': categoria,
                    'palabras_clave': self._extract_keywords(row['pregunta'])
                }
                faqs.append(faq)
                self.all_faqs_flat.append(faq)
                self.faq_index[faq['id']] = faq

            self.faqs_by_category[categoria] = faqs

    def _extract_keywords(self, pregunta: str) -> List[str]:
        """Extrae palabras clave de una pregunta para búsqueda rápida."""
        # Convertir a minúsculas y remover puntuación
        pregunta_limpia = pregunta.lower()
        pregunta_limpia = re.sub(r'[¿?¡!.,;:]', '', pregunta_limpia)

        # Palabras vacías en español que ignorar
        stop_words = {'el', 'la', 'de', 'que', 'y', 'o', 'un', 'una', 'en', 'por', 'para', 'con', 'sin', 'a', 'es'}

        # Extraer palabras
        palabras = pregunta_limpia.split()
        palabras_clave = [p for p in palabras if p not in stop_words and len(p) > 2]

        return palabras_clave

    def search_faqs(self, pregunta: str, top_k: int = 3) -> List[Tuple[Dict, float]]:
        """
        Busca FAQs relevantes usando similitud de palabras clave.

        Args:
            pregunta: Pregunta del usuario
            top_k: Número de resultados a retornar

        Returns:
            Lista de tuplas (faq, score_similitud) ordenadas por relevancia
        """
        palabras_pregunta = self._extract_keywords(pregunta)

        if not palabras_pregunta:
            # Si no hay palabras clave, retornar FAQs aleatorios
            return [(faq, 0.0) for faq in self.all_faqs_flat[:top_k]]

        resultados = []

        for faq in self.all_faqs_flat:
            # Calcular similitud basada en palabras clave comunes
            palabras_comunes = set(palabras_pregunta) & set(faq['palabras_clave'])
            score = len(palabras_comunes) / max(len(palabras_pregunta), len(faq['palabras_clave']))

            resultados.append((faq, score))

        # Ordenar por score descendente
        resultados.sort(key=lambda x: x[1], reverse=True)

        return resultados[:top_k]

    def get_categories(self) -> List[str]:
        """Retorna lista de categorías disponibles."""
        return sorted(list(self.faqs_by_category.keys()))

    def get_faqs_by_category(self, categoria: str) -> List[Dict]:
        """Retorna FAQs de una categoría específica."""
        return self.faqs_by_category.get(categoria, [])

    def get_all_faqs(self) -> List[Dict]:
        """Retorna todas las FAQs."""
        return self.all_faqs_flat

    def get_faq_by_id(self, faq_id: int) -> Dict:
        """Retorna una FAQ específica por ID."""
        return self.faq_index.get(faq_id)

    def export_to_json(self, output_path: str = "data/faqs.json") -> None:
        """Exporta las FAQs a formato JSON."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.faqs_by_category, f, ensure_ascii=False, indent=2)

    def get_statistics(self) -> Dict:
        """Retorna estadísticas sobre las FAQs cargadas."""
        return {
            'total_faqs': len(self.all_faqs_flat),
            'total_categorias': len(self.faqs_by_category),
            'categorias': {
                cat: len(faqs)
                for cat, faqs in self.faqs_by_category.items()
            }
        }


if __name__ == "__main__":
    # Ejemplo de uso
    loader = FAQLoader()

    # Mostrar estadísticas
    stats = loader.get_statistics()
    print("Estadísticas de FAQs:")
    print(f"  Total de FAQs: {stats['total_faqs']}")
    print(f"  Total de categorías: {stats['total_categorias']}")
    print("\nFAQs por categoría:")
    for cat, count in stats['categorias'].items():
        print(f"  {cat}: {count}")

    # Probar búsqueda
    print("\n\nBúsqueda de ejemplo - 'usuario':")
    resultados = loader.search_faqs("usuario")
    for faq, score in resultados:
        print(f"  [{score:.2f}] {faq['pregunta']}")
