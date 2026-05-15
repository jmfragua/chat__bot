#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "   🚀 Iniciando Asistente de Nómina y Contratación"
echo "════════════════════════════════════════════════════════════"
echo ""

# Activar entorno virtual
source venv/bin/activate

# Verificar que la clave de OpenAI esté configurada
if grep -q "sk-proj" .env; then
    echo "✅ Clave de OpenAI detectada"
else
    echo "❌ Error: OPENAI_API_KEY no configurada en .env"
    exit 1
fi

# Verificar que Excel exista
if [ -f "FAQ_Chatbot_Nomina.xlsx" ]; then
    echo "✅ Base de FAQs detectada (29 FAQs cargadas)"
else
    echo "❌ Error: FAQ_Chatbot_Nomina.xlsx no encontrado"
    exit 1
fi

echo ""
echo "Iniciando Streamlit..."
echo "La aplicación se abrirá automáticamente en: http://localhost:8501"
echo ""
echo "📝 Consejos de uso:"
echo "  • Escribe tu pregunta en el campo de entrada"
echo "  • Las respuestas se basan en FAQs de nómina y contratación"
echo "  • Usa el botón 'Reiniciar Chat' para limpiar el historial"
echo "  • El panel lateral muestra estadísticas y categorías"
echo ""
echo "🛑 Para detener: presiona Ctrl+C"
echo "════════════════════════════════════════════════════════════"
echo ""

streamlit run app.py
