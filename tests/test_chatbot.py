"""
Script de evaluación automática del chatbot.
Prueba el chatbot con preguntas predefinidas y mide su precisión y comportamiento.
"""

import sys
sys.path.insert(0, '..')

from src.faq_loader import FAQLoader
from src.llm_handler import LLMHandler
from src.guardrails import GuardrailValidator
from src.chatbot_engine import ChatbotEngine
from typing import Dict, List
import json


class ChatbotEvaluator:
    """Evalúa el desempeño del chatbot con test cases predefinidos."""

    # Casos de prueba con preguntas, categoría esperada y si debe estar en FAQs
    TEST_CASES = [
        {
            'pregunta': '¿Cómo puedo recuperar mi usuario o contraseña?',
            'categoria_esperada': 'General',
            'debe_estar_en_faqs': True,
            'tipo': 'faq_exacta'
        },
        {
            'pregunta': '¿Cuáles son los requisitos para retirar mis cesantías?',
            'categoria_esperada': 'General',
            'debe_estar_en_faqs': True,
            'tipo': 'faq_exacta'
        },
        {
            'pregunta': '¿Por qué recibí un pago menor en la segunda quincena?',
            'categoria_esperada': 'General',
            'debe_estar_en_faqs': True,
            'tipo': 'faq_similar'
        },
        {
            'pregunta': '¿Cuándo se paga el auxilio de transporte?',
            'categoria_esperada': 'Beneficios',
            'debe_estar_en_faqs': True,
            'tipo': 'faq_exacta'
        },
        {
            'pregunta': '¿Cómo puedo solicitar una certificación laboral?',
            'categoria_esperada': 'Certificaciones',
            'debe_estar_en_faqs': True,
            'tipo': 'faq_exacta'
        },
        {
            'pregunta': '¿Puedo dividir mis vacaciones en varios periodos?',
            'categoria_esperada': 'Vacaciones y Licencias',
            'debe_estar_en_faqs': True,
            'tipo': 'faq_exacta'
        },
        {
            'pregunta': '¿Cómo actualizo mi EPS o fondo de pensiones?',
            'categoria_esperada': 'Seguridad Social',
            'debe_estar_en_faqs': True,
            'tipo': 'faq_similar'
        },
        {
            'pregunta': '¿Qué documentos necesito para vinculación?',
            'categoria_esperada': 'Contratación',
            'debe_estar_en_faqs': True,
            'tipo': 'faq_similar'
        },
        {
            'pregunta': '¿Receta para hacer tamales?',
            'categoria_esperada': 'Fuera de Alcance',
            'debe_estar_en_faqs': False,
            'tipo': 'fuera_de_dominio'
        },
        {
            'pregunta': '¿Cuál es el salario mínimo en Colombia?',
            'categoria_esperada': 'General',
            'debe_estar_en_faqs': True,
            'tipo': 'faq_general'
        }
    ]

    def __init__(self):
        """Inicializa el evaluador."""
        try:
            self.loader = FAQLoader()
            self.llm_handler = LLMHandler()
            self.validator = GuardrailValidator(self.loader.get_categories())
            self.chatbot = ChatbotEngine(
                self.loader,
                self.llm_handler,
                self.validator
            )
            self.resultados = []
        except Exception as e:
            print(f"❌ Error al inicializar evaluador: {e}")
            raise

    def evaluate_response(self, test_case: Dict) -> Dict:
        """
        Evalúa una respuesta del chatbot.

        Args:
            test_case: Caso de prueba con pregunta y expectativas

        Returns:
            Dict con resultados de evaluación
        """
        pregunta = test_case['pregunta']
        categoria_esperada = test_case['categoria_esperada']
        debe_estar_en_faqs = test_case['debe_estar_en_faqs']
        tipo_prueba = test_case['tipo']

        # Procesar pregunta
        resultado = self.chatbot.process_question(pregunta)

        respuesta = resultado['respuesta']
        categoria = resultado['categoria']
        exito = resultado['exito']
        confianza = resultado['confianza']

        # Evaluar resultado
        evaluacion = {
            'pregunta': pregunta,
            'tipo': tipo_prueba,
            'categoria_esperada': categoria_esperada,
            'categoria_obtenida': categoria,
            'categoria_correcta': categoria == categoria_esperada,
            'debe_estar_en_faqs': debe_estar_en_faqs,
            'encontrada_en_faqs': exito,
            'respuesta_correcta': exito == debe_estar_en_faqs,
            'confianza': confianza,
            'respuesta': respuesta[:100] + "..." if len(respuesta) > 100 else respuesta,
            'puntuacion': 0
        }

        # Calcular puntuación
        if evaluacion['respuesta_correcta']:
            evaluacion['puntuacion'] += 50

        if evaluacion['categoria_correcta']:
            evaluacion['puntuacion'] += 30

        if confianza > 0.7:
            evaluacion['puntuacion'] += 20

        return evaluacion

    def run_evaluation(self) -> Dict:
        """
        Ejecuta la evaluación completa del chatbot.

        Returns:
            Dict con resultados de evaluación
        """
        print("=" * 80)
        print("EVALUACIÓN AUTOMÁTICA DEL CHATBOT")
        print("=" * 80)
        print(f"\nEjecutando {len(self.TEST_CASES)} casos de prueba...\n")

        total_puntuacion = 0

        for i, test_case in enumerate(self.TEST_CASES, 1):
            print(f"[{i}/{len(self.TEST_CASES)}] {test_case['pregunta'][:60]}...")

            evaluacion = self.evaluate_response(test_case)
            self.resultados.append(evaluacion)

            total_puntuacion += evaluacion['puntuacion']

            # Mostrar indicador de éxito
            if evaluacion['respuesta_correcta']:
                print(f"  ✓ EXITOSA | Categoría: {evaluacion['categoria_obtenida']} | "
                      f"Confianza: {evaluacion['confianza']:.2f}")
            else:
                print(f"  ✗ FALLIDA | Esperado: {evaluacion['categoria_esperada']} | "
                      f"Obtenido: {evaluacion['categoria_obtenida']}")

        # Calcular estadísticas
        total_casos = len(self.resultados)
        exitosas = sum(1 for r in self.resultados if r['respuesta_correcta'])
        categoria_correctas = sum(1 for r in self.resultados if r['categoria_correcta'])
        confianza_promedio = sum(r['confianza'] for r in self.resultados) / total_casos

        puntuacion_promedio = total_puntuacion / (total_casos * 100) * 100

        # Imprimir resultados
        print("\n" + "=" * 80)
        print("RESULTADOS FINALES")
        print("=" * 80)

        print(f"\n📊 Estadísticas Generales:")
        print(f"  • Total de casos: {total_casos}")
        print(f"  • Respuestas correctas: {exitosas}/{total_casos} ({exitosas/total_casos*100:.1f}%)")
        print(f"  • Categorías correctas: {categoria_correctas}/{total_casos} ({categoria_correctas/total_casos*100:.1f}%)")
        print(f"  • Confianza promedio: {confianza_promedio:.2f}")
        print(f"  • Puntuación promedio: {puntuacion_promedio:.1f}/100")

        # Desglose por tipo de prueba
        print(f"\n🔍 Resultados por Tipo de Prueba:")
        tipos = {}
        for resultado in self.resultados:
            tipo = resultado['tipo']
            if tipo not in tipos:
                tipos[tipo] = {'total': 0, 'exitosas': 0}
            tipos[tipo]['total'] += 1
            if resultado['respuesta_correcta']:
                tipos[tipo]['exitosas'] += 1

        for tipo, stats in tipos.items():
            tasa = stats['exitosas'] / stats['total'] * 100
            print(f"  • {tipo}: {stats['exitosas']}/{stats['total']} ({tasa:.1f}%)")

        # Casos fallidos
        fallidos = [r for r in self.resultados if not r['respuesta_correcta']]
        if fallidos:
            print(f"\n⚠️  Casos Fallidos ({len(fallidos)}):")
            for fallido in fallidos:
                print(f"  • {fallido['pregunta'][:50]}...")
                print(f"    Esperado: {fallido['categoria_esperada']}")
                print(f"    Obtenido: {fallido['categoria_obtenida']}")

        return {
            'total_casos': total_casos,
            'exitosas': exitosas,
            'tasa_exito': exitosas / total_casos * 100,
            'categoria_correctas': categoria_correctas,
            'confianza_promedio': confianza_promedio,
            'puntuacion_promedio': puntuacion_promedio,
            'resultados_detallados': self.resultados
        }

    def export_results(self, output_file: str = "evaluation_results.json") -> None:
        """
        Exporta resultados a archivo JSON.

        Args:
            output_file: Ruta del archivo de salida
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.resultados, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Resultados exportados a: {output_file}")


def main():
    """Función principal para ejecutar evaluación."""
    try:
        evaluator = ChatbotEvaluator()
        resultados = evaluator.run_evaluation()
        evaluator.export_results()

        # Mostrar resumen final
        print("\n" + "=" * 80)
        print(f"✅ EVALUACIÓN COMPLETADA")
        print(f"   Puntuación Final: {resultados['puntuacion_promedio']:.1f}/100")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error durante evaluación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
