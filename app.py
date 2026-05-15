"""
Interfaz principal del chatbot con Streamlit.
Una única pantalla que permite interactuar con el asistente de FAQs.
"""

import streamlit as st
from streamlit_option_menu import option_menu
import os
from datetime import datetime
import uuid
from dotenv import load_dotenv

from src.faq_loader import FAQLoader
from src.llm_handler import LLMHandler
from src.guardrails import GuardrailValidator
from src.chatbot_engine import ChatbotEngine
from src.logger import ChatLogger

# Cargar variables de entorno
load_dotenv()

# Configuración de página
st.set_page_config(
    page_title="Asistente de Nómina y Contratación",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados - Mejorados para mejor contraste
st.markdown("""
    <style>
    /* Header principal */
    .main-header {
        color: #0d47a1;
        text-align: center;
        margin-bottom: 30px;
        font-size: 2.5em;
        font-weight: bold;
    }

    /* Mensaje del usuario - Burbuja */
    .message-user {
        background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 18px;
        color: #fff;
        font-weight: 500;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    /* Mensaje del bot - Burbuja */
    .message-bot {
        background-color: #f0f0f0;
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 18px;
        color: #000;
        line-height: 1.6;
        max-width: 80%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    /* Footer */
    .footer {
        text-align: center;
        margin-top: 50px;
        color: #666;
        border-top: 2px solid #ddd;
        padding-top: 20px;
    }

    /* Input de texto mejorado */
    .stTextInput > div > div > input {
        background-color: #fff !important;
        color: #000 !important;
        font-size: 16px !important;
        caret-color: #1976d2 !important;
    }

    /* Botones mejorados */
    .stButton > button {
        background-color: #1976d2 !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 5px !important;
        padding: 12px 20px !important;
        height: auto !important;
        min-height: 44px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: normal !important;
        font-size: 14px !important;
    }

    .stButton > button:hover {
        background-color: #0d47a1 !important;
    }

    /* Botones de copiar estilo secundario */
    .stButton button[kind="secondary"] {
        background-color: #f0f0f0 !important;
        color: #333 !important;
        border: 1px solid #ddd !important;
        padding: 8px 12px !important;
    }

    /* Botones de copiar en categorías - más visibles */
    .stColumns button {
        background-color: #1976d2 !important;
        color: white !important;
        font-size: 16px !important;
        padding: 6px 10px !important;
        border-radius: 4px !important;
    }

    .stColumns button:hover {
        background-color: #0d47a1 !important;
    }

    /* Botones de sugerencias */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3) !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(25, 118, 210, 0.4) !important;
    }

    /* Área de chat mejorada */
    .chat-container {
        background-color: #fafafa;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
    }

    /* Expansores mejorados */
    .streamlit-expanderHeader {
        background-color: #f0f0f0 !important;
        color: #000 !important;
    }

    /* Métricas mejoradas */
    .metric-card {
        background-color: #f9f9f9 !important;
        border: 1px solid #ddd !important;
        border-radius: 8px !important;
        padding: 15px !important;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_chatbot():
    """Inicializa los componentes del chatbot una sola vez."""
    try:
        faq_loader = FAQLoader("FAQ_Chatbot_Nomina.xlsx")
        llm_handler = LLMHandler()
        validator = GuardrailValidator(faq_loader.get_categories())
        chatbot = ChatbotEngine(faq_loader, llm_handler, validator)
        logger = ChatLogger()

        return {
            'chatbot': chatbot,
            'logger': logger,
            'faq_loader': faq_loader,
            'initialized': True
        }
    except Exception as e:
        st.error(f"❌ Error al inicializar el chatbot: {str(e)}")
        return {'initialized': False, 'error': str(e)}


def main():
    """Función principal de la aplicación."""

    # Header principal
    st.markdown("""
        <h1 class='main-header'>💼 Asistente de Nómina y Contratación</h1>
    """, unsafe_allow_html=True)

    st.markdown(
        "Bienvenido al asistente virtual. Puedo ayudarte con preguntas sobre "
        "**nómina, beneficios, vacaciones, certificaciones y contratación**. 🤖"
    )

    # Inicializar componentes
    components = initialize_chatbot()

    if not components['initialized']:
        st.error(f"Error fatal: {components['error']}")
        st.info("Por favor, asegúrate de que:")
        st.info("1. El archivo 'FAQ_Chatbot_Nomina.xlsx' exista en la carpeta raíz")
        st.info("2. La variable de entorno OPENAI_API_KEY esté configurada")
        return

    chatbot = components['chatbot']
    logger = components['logger']

    # ===== SIDEBAR =====
    with st.sidebar:
        st.markdown("### ⚙️ Panel de Control")

        # Crear o recuperar ID de sesión
        if 'session_id' not in st.session_state:
            st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"
            logger.create_session(st.session_state.session_id)

        st.markdown(f"**ID Sesión:** `{st.session_state.session_id}`")

        # Botón para reiniciar conversación
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("🔄 Reiniciar\nChat", use_container_width=True, key="btn_reiniciar"):
                chatbot.reset_conversation()
                st.session_state.messages = []
                st.success("Chat reiniciado ✓")
                st.rerun()

        with col2:
            if st.button("📊 Estadísticas", use_container_width=True, key="btn_stats"):
                st.session_state.show_stats = not st.session_state.get('show_stats', False)
                st.rerun()

        # Mostrar categorías disponibles - INTERACTIVAS
        st.markdown("### 📚 Categorías Disponibles")
        categorias = chatbot.get_available_categories()

        for categoria in categorias:
            with st.expander(f"📂 {categoria}", expanded=False):
                # Obtener FAQs de esta categoría
                faqs_categoria = components['faq_loader'].get_faqs_by_category(categoria)

                if faqs_categoria:
                    st.markdown(f"**{len(faqs_categoria)} preguntas disponibles**\n")

                    for idx, faq in enumerate(faqs_categoria, 1):
                        col_pregunta, col_enviar = st.columns([4, 1])

                        with col_pregunta:
                            st.markdown(f"{idx}. {faq['pregunta']}")

                        with col_enviar:
                            if st.button("➡️", key=f"send_{faq['id']}", help="Enviar pregunta"):
                                st.session_state.messages.append({'role': 'user', 'content': faq['pregunta']})
                                with st.spinner("🤔 Procesando tu pregunta..."):
                                    resultado = chatbot.process_question(faq['pregunta'])
                                    respuesta = resultado['respuesta']
                                    categoria = resultado.get('categoria', 'N/A')
                                    confianza = resultado.get('confianza', 0)
                                    exito = resultado.get('exito', False)

                                    logger.log_interaction(
                                        st.session_state.session_id,
                                        faq['pregunta'],
                                        respuesta,
                                        categoria,
                                        confianza,
                                        exito
                                    )

                                st.session_state.messages.append({'role': 'assistant', 'content': respuesta})
                                st.rerun()
                else:
                    st.info("No hay preguntas en esta categoría")

        # Mostrar información de FAQs
        stats_faq = components['faq_loader'].get_statistics()
        st.markdown("### 📈 Base de FAQs")
        st.markdown(f"**Total de FAQs:** {stats_faq['total_faqs']}")
        st.markdown(f"**Categorías:** {stats_faq['total_categorias']}")

        # Footer en sidebar
        st.markdown("---")
        st.markdown(
            "**Powered by OpenAI GPT-4o-mini**  \n"
            "Versión 1.0 | Mayo 2026"
        )

    # ===== ÁREA PRINCIPAL =====

    # Inicializar estado de sesión para mensajes
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Mostrar historial de mensajes (solo si hay mensajes)
    if st.session_state.messages:
        chat_container = st.container()

        with chat_container:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for message in st.session_state.messages:
                if message['role'] == 'user':
                    col1, col2 = st.columns([1, 10])
                    with col1:
                        st.markdown("👤")
                    with col2:
                        st.markdown(
                            f"<div class='message-user'>{message['content']}</div>",
                            unsafe_allow_html=True
                        )
                else:
                    col1, col2 = st.columns([1, 10])
                    with col1:
                        st.markdown("🤖")
                    with col2:
                        st.markdown(
                            f"<div class='message-bot'>{message['content']}</div>",
                            unsafe_allow_html=True
                        )
            st.markdown('</div>', unsafe_allow_html=True)

    # Formulario de entrada
    st.markdown("---")
    st.markdown("### ✍️ Tu Pregunta")

    with st.form("question_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])

        with col1:
            user_input = st.text_input(
                "Escribe tu pregunta aquí:",
                placeholder="Ej: ¿Cómo puedo recuperar mi usuario?",
                label_visibility="collapsed"
            )

        with col2:
            submit_button = st.form_submit_button("Enviar", use_container_width=True)

    # Sugerencias de preguntas frecuentes
    st.markdown("**💡 Preguntas sugeridas:**")
    suggested_questions = [
        "¿Cómo puedo recuperar mi usuario o contraseña en MiNómina?",
        "¿Cómo puedo descargar mis comprobantes o colillas de pago?",
        "¿Cómo puedo solicitar una certificación o carta laboral?",
        "¿Cómo actualizar mi EPS o fondo de pensiones?",
        "¿Cuál es el salario mínimo en Colombia?",
        "¿Por qué me descuentan salud y pensión?"
    ]

    cols = st.columns(3)
    for idx, question in enumerate(suggested_questions):
        with cols[idx % 3]:
            if st.button(f"📌 {question}", use_container_width=True, key=f"suggest_{idx}"):
                st.session_state.messages.append({'role': 'user', 'content': question})

                with st.spinner("🤔 Procesando tu pregunta..."):
                    resultado = chatbot.process_question(question)
                    respuesta = resultado['respuesta']
                    categoria = resultado.get('categoria', 'N/A')
                    confianza = resultado.get('confianza', 0)
                    exito = resultado.get('exito', False)

                    logger.log_interaction(
                        st.session_state.session_id,
                        question,
                        respuesta,
                        categoria,
                        confianza,
                        exito
                    )

                st.session_state.messages.append({'role': 'assistant', 'content': respuesta})
                st.rerun()

    # Procesar pregunta
    if submit_button and user_input:
        # Añadir pregunta del usuario al historial de UI
        st.session_state.messages.append({
            'role': 'user',
            'content': user_input
        })

        # Procesar con el chatbot
        with st.spinner("🤔 Procesando tu pregunta..."):
            resultado = chatbot.process_question(user_input)

            respuesta = resultado['respuesta']
            categoria = resultado.get('categoria', 'N/A')
            confianza = resultado.get('confianza', 0)
            exito = resultado.get('exito', False)

            # Registrar en logger
            logger.log_interaction(
                st.session_state.session_id,
                user_input,
                respuesta,
                categoria,
                confianza,
                exito
            )

        # Añadir respuesta del bot al historial de UI
        st.session_state.messages.append({
            'role': 'assistant',
            'content': respuesta
        })

        # Mostrar información de respuesta
        with st.expander("📋 Detalles de la respuesta", expanded=True):
            st.markdown("---")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"**📂 Categoría**")
                st.markdown(f"<div style='background-color: #e3f2fd; padding: 10px; border-radius: 5px; color: #000; font-weight: bold;'>{categoria}</div>", unsafe_allow_html=True)

            with col2:
                st.markdown(f"**📊 Confianza**")
                confianza_pct = f"{confianza:.0%}"
                color = "#4caf50" if confianza > 0.7 else "#ff9800"
                st.markdown(f"<div style='background-color: {color}; padding: 10px; border-radius: 5px; color: white; font-weight: bold; text-align: center;'>{confianza_pct}</div>", unsafe_allow_html=True)

            with col3:
                st.markdown(f"**✅ Estado**")
                estado_text = "✓ Exitosa" if exito else "✗ Fuera de alcance"
                estado_color = "#4caf50" if exito else "#ff9800"
                st.markdown(f"<div style='background-color: {estado_color}; padding: 10px; border-radius: 5px; color: white; font-weight: bold; text-align: center;'>{estado_text}</div>", unsafe_allow_html=True)
            st.markdown("---")

        # Recargar interfaz con input limpio
        st.rerun()

    # Mostrar estadísticas si está habilitado
    if st.session_state.get('show_stats', False):
        st.markdown("---")
        st.markdown("### 📊 Estadísticas de la Sesión")

        stats = chatbot.get_statistics()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Preguntas",
                stats['total_preguntas'],
                delta=None
            )

        with col2:
            st.metric(
                "Exitosas",
                stats['preguntas_exitosas']
            )

        with col3:
            st.metric(
                "Tasa de Éxito",
                f"{stats['tasa_exito']:.1f}%"
            )

        with col4:
            st.metric(
                "Confianza Promedio",
                f"{stats['confianza_promedio']:.2f}"
            )

        # Mostrar categorías consultadas
        if stats['categorias_consultadas']:
            st.subheader("Categorías Consultadas")
            for categoria, count in stats['categorias_consultadas'].items():
                st.write(f"• {categoria}: {count}")

    # Footer
    st.markdown("""
        <div class='footer'>
        <p>💼 <strong>Asistente de Nómina y Contratación</strong></p>
        <p>Para soporte directo, contacta con el equipo de RH</p>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
