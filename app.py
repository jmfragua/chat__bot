import re
import unicodedata

import streamlit as st

FAQS = [
    {
        "categoria": "Nómina",
        "pregunta": "¿Cuándo se paga la nómina mensual?",
        "respuesta": "La nómina se abona el último día hábil de cada mes.",
    },
    {
        "categoria": "Nómina",
        "pregunta": "¿Cómo se calculan las horas extra?",
        "respuesta": "Las horas extra se calculan según convenio y se reflejan en la nómina del mes siguiente.",
    },
    {
        "categoria": "Nómina",
        "pregunta": "¿Qué hago si detecto un error en mi nómina?",
        "respuesta": "Debes abrir una incidencia con RR. HH. antes de 5 días hábiles tras recibir la nómina.",
    },
    {
        "categoria": "Contratación",
        "pregunta": "¿Qué documentos necesito para firmar contrato?",
        "respuesta": "Necesitas DNI/NIE, número de afiliación a la Seguridad Social y datos bancarios.",
    },
    {
        "categoria": "Contratación",
        "pregunta": "¿Cuánto dura el periodo de prueba?",
        "respuesta": "El periodo de prueba depende del convenio y del tipo de contrato, normalmente entre 1 y 6 meses.",
    },
    {
        "categoria": "Contratación",
        "pregunta": "¿Se puede cambiar de contrato temporal a indefinido?",
        "respuesta": "Sí, tras evaluación del desempeño y necesidades del área, RR. HH. puede formalizar la conversión.",
    },
]


def _normalizar(texto: str) -> set[str]:
    texto_normalizado = unicodedata.normalize("NFD", texto.lower())
    texto_sin_acentos = "".join(c for c in texto_normalizado if unicodedata.category(c) != "Mn")
    return set(re.findall(r"[a-z0-9]+", texto_sin_acentos))


def buscar_respuesta(pregunta_usuario: str) -> tuple[str, str]:
    tokens_usuario = _normalizar(pregunta_usuario)

    mejor_faq = None
    mejor_puntuacion = 0

    for faq in FAQS:
        tokens_faq = _normalizar(faq["pregunta"])
        puntuacion = len(tokens_usuario & tokens_faq)
        if puntuacion > mejor_puntuacion:
            mejor_puntuacion = puntuacion
            mejor_faq = faq

    if mejor_puntuacion == 0 or not mejor_faq:
        return (
            "No tengo una respuesta exacta para esa consulta. "
            "Prueba con una pregunta sobre nómina o contratación.",
            "General",
        )

    return mejor_faq["respuesta"], mejor_faq["categoria"]


def main() -> None:
    st.set_page_config(page_title="FAQ Nómina y Contratación", page_icon="🤖", layout="wide")

    st.title("🤖 Chatbot inteligente de RR. HH.")
    st.caption("Resuelve dudas frecuentes de nómina y contratación en segundos")

    total_faqs = len(FAQS)
    total_nomina = sum(1 for faq in FAQS if faq["categoria"] == "Nómina")
    total_contratacion = sum(1 for faq in FAQS if faq["categoria"] == "Contratación")

    col1, col2, col3 = st.columns(3)
    col1.metric("FAQs totales", total_faqs)
    col2.metric("FAQs de nómina", total_nomina)
    col3.metric("FAQs de contratación", total_contratacion)

    st.sidebar.header("Preguntas sugeridas")
    sugeridas = [faq["pregunta"] for faq in FAQS]
    pregunta_rapida = None
    for i, pregunta in enumerate(sugeridas, start=1):
        if st.sidebar.button(f"{i}. {pregunta}", use_container_width=True):
            pregunta_rapida = pregunta

    st.sidebar.info("Tip: también puedes escribir tu pregunta en el chat.")

    if "historial" not in st.session_state:
        st.session_state.historial = [
            {
                "role": "assistant",
                "content": "¡Hola! Soy tu asistente de FAQs de nómina y contratación. ¿En qué te ayudo?",
            }
        ]

    for mensaje in st.session_state.historial:
        with st.chat_message(mensaje["role"]):
            st.markdown(mensaje["content"])

    entrada_usuario = pregunta_rapida or st.chat_input("Escribe tu pregunta")

    if entrada_usuario:
        st.session_state.historial.append({"role": "user", "content": entrada_usuario})
        with st.chat_message("user"):
            st.markdown(entrada_usuario)

        respuesta, categoria = buscar_respuesta(entrada_usuario)
        texto_respuesta = f"**[{categoria}]** {respuesta}"
        st.session_state.historial.append({"role": "assistant", "content": texto_respuesta})

        with st.chat_message("assistant"):
            st.markdown(texto_respuesta)


if __name__ == "__main__":
    main()
