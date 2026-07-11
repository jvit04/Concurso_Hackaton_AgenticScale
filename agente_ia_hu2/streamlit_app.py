"""
streamlit_app.py
------------------
Interfaz gráfica (Streamlit) para el Tutor IA de Futuro Academy (HU2).

No modifica la lógica de agent_tutor.py / base_conocimiento.py: solo la
consume. Así, este archivo es "opcional" — el CLI y los endpoints FastAPI
siguen funcionando igual si el equipo prefiere otra interfaz.

Cómo correrlo:
    export GEMINI_API_KEY="tu_api_key"
    streamlit run hu2_tutor_financiero/streamlit_app.py

Nota sobre la ruta de ejecución: este archivo agrega la raíz del proyecto al
sys.path automáticamente, así que funciona sin importar desde qué carpeta
ejecutes el comando `streamlit run`, siempre que `shared/` viva en la raíz
del proyecto (un nivel arriba de hu2_tutor_financiero/).
"""

import os
import subprocess
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Asegurar que la raíz del proyecto esté en sys.path (para poder importar
# `agente_ia_hu2` y `shared` sin importar el cwd desde el que se ejecute).
# --------------------------------------------------------------------------
_RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, _RAIZ_PROYECTO)

import streamlit as st
from streamlit.runtime.scriptrunner_utils.script_run_context import get_script_run_ctx

if get_script_run_ctx() is None:
    script_path = Path(__file__).resolve()
    comando = [sys.executable, "-m", "streamlit", "run", str(script_path)]
    print(f"Iniciando Streamlit con: {' '.join(comando)}")
    raise SystemExit(subprocess.call(comando))

try:
    from agente_ia_hu2.agent_tutor import (
        evaluar_quiz,
        iniciar_quiz,
        obtener_o_crear_sesion,
        procesar_mensaje,
    )
    from agente_ia_hu2.base_conocimiento import BASE_CONOCIMIENTO, obtener_tema
except ModuleNotFoundError:  # Compatibilidad con ejecuciones directas desde la carpeta del módulo
    from agent_tutor import (
        evaluar_quiz,
        iniciar_quiz,
        obtener_o_crear_sesion,
        procesar_mensaje,
    )
    from base_conocimiento import BASE_CONOCIMIENTO, obtener_tema

st.set_page_config(page_title="Tutor IA · Futuro Academy", page_icon="🎓", layout="centered")

st.markdown(
    """
    <style>
    :root {
        --background-color: #f7f9fc;
        --card-color: #ffffff;
        --primary-color: #2563eb;
        --primary-color-dark: #1d4ed8;
        --text-color: #0f172a;
        --muted-color: #475569;
        --border-color: #dbe4f0;
    }
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    .stSidebar {
        background-color: #f1f5f9;
        border-right: 1px solid var(--border-color);
    }
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 8px;
        border: 1px solid var(--primary-color-dark);
    }
    .stButton > button:hover {
        background-color: var(--primary-color-dark);
        color: white;
    }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px;
    }
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #64748b !important;
    }
    .stAlert, .stInfo, .stSuccess, .stWarning, .stError {
        border-radius: 10px;
    }
    .stApp, .stApp p, .stApp div, .stApp span, .stApp label {
        color: #000000 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# Estado de la sesión de Streamlit
# --------------------------------------------------------------------------
# Streamlit vuelve a ejecutar todo el script en cada interacción, así que
# guardamos en st.session_state: la SesionTutor (lógica de negocio), el
# historial de chat (solo para pintar la UI) y el estado del quiz.

def _inicializar_estado():
    if "email" not in st.session_state:
        st.session_state.email = ""
    if "sesion_id" not in st.session_state:
        st.session_state.sesion_id = None
    if "historial" not in st.session_state:
        st.session_state.historial = []  # lista de {"role": "user"/"assistant", "content": str}
    if "quiz_preguntas" not in st.session_state:
        st.session_state.quiz_preguntas = None  # lista de preguntas activas, o None
    if "quiz_meta" not in st.session_state:
        st.session_state.quiz_meta = None  # {"nombre_visible":..., "fuente":...}


def _obtener_sesion():
    """Crea (o recupera) la SesionTutor asociada a esta sesión de Streamlit."""
    sesion = obtener_o_crear_sesion(
        session_id=st.session_state.sesion_id,
        email=st.session_state.email or None,
    )
    st.session_state.sesion_id = sesion.session_id
    return sesion


def _agregar_al_historial(role: str, content: str):
    st.session_state.historial.append({"role": role, "content": content})


def _reiniciar_conversacion():
    st.session_state.sesion_id = None
    st.session_state.historial = []
    st.session_state.quiz_preguntas = None
    st.session_state.quiz_meta = None


_inicializar_estado()
sesion = _obtener_sesion()


# --------------------------------------------------------------------------
# Barra lateral: identidad, estado de Gemini y acceso directo a temas
# --------------------------------------------------------------------------

with st.sidebar:
    st.header("🎓 Tutor IA")
    st.caption("Futuro Academy — HU2")

    nuevo_email = st.text_input(
        "Tu correo (opcional)",
        value=st.session_state.email,
        placeholder="juan@correo.com",
        help="Si lo ingresas, tu interés puede registrarse en el CRM con tu consentimiento.",
    )
    if nuevo_email != st.session_state.email:
        st.session_state.email = nuevo_email
        st.rerun()

    st.divider()

    if os.getenv("GEMINI_API_KEY"):
        st.success("GEMINI_API_KEY configurada ✅")
    else:
        st.warning(
            "GEMINI_API_KEY no configurada. El Tutor seguirá funcionando "
            "usando el contenido aprobado directamente, sin redacción de Gemini."
        )

    st.divider()
    st.subheader("Temas disponibles")
    for tema_id, tema in BASE_CONOCIMIENTO.items():
        if st.button(tema["nombre_visible"], use_container_width=True, key=f"btn_tema_{tema_id}"):
            _agregar_al_historial("user", tema["nombre_visible"])
            resultado = procesar_mensaje(sesion, tema["nombre_visible"])
            _agregar_al_historial("assistant", resultado["respuesta"])
            st.rerun()

    st.divider()
    if st.button("🔄 Reiniciar conversación", use_container_width=True):
        _reiniciar_conversacion()
        st.rerun()


# --------------------------------------------------------------------------
# Encabezado principal
# --------------------------------------------------------------------------

st.title("🎓 Tutor Financiero IA")
st.caption(
    "Aprende conceptos financieros aprobados por Futuro Academy antes de "
    "solicitar asesoría personalizada."
)

if sesion.tema_actual:
    tema_activo = obtener_tema(sesion.tema_actual)
    st.info(f"📘 Tema activo: **{tema_activo['nombre_visible']}** · Fuente: {tema_activo['fuente']}")


# --------------------------------------------------------------------------
# Historial de chat
# --------------------------------------------------------------------------

if not st.session_state.historial:
    st.chat_message("assistant").write(
        "¡Hola! Soy el Tutor IA de Futuro Academy 👋 Puedes preguntarme por un "
        "tema (ej. *\"quiero aprender sobre interés compuesto\"*) o elegir uno "
        "en el menú lateral."
    )

for turno in st.session_state.historial:
    st.chat_message(turno["role"]).write(turno["content"])


# --------------------------------------------------------------------------
# Formulario de consentimiento (botones en vez de escribir sí/no)
# --------------------------------------------------------------------------

if sesion.esperando_consentimiento and st.session_state.quiz_preguntas is None:
    st.write("**¿Confirmas el registro de tu interés en el CRM?**")
    col_si, col_no = st.columns(2)
    with col_si:
        if st.button("✅ Sí, autorizo", use_container_width=True):
            _agregar_al_historial("user", "Sí, autorizo")
            resultado = procesar_mensaje(sesion, "sí")
            _agregar_al_historial("assistant", resultado["respuesta"])
            st.rerun()
    with col_no:
        if st.button("❌ No, gracias", use_container_width=True):
            _agregar_al_historial("user", "No, gracias")
            resultado = procesar_mensaje(sesion, "no")
            _agregar_al_historial("assistant", resultado["respuesta"])
            st.rerun()


# --------------------------------------------------------------------------
# Formulario del quiz (3 preguntas de opción múltiple)
# --------------------------------------------------------------------------

if st.session_state.quiz_preguntas is not None:
    meta = st.session_state.quiz_meta
    st.subheader(f"📝 Quiz: {meta['nombre_visible']}")
    st.caption(f"Fuente: {meta['fuente']}")

    with st.form("form_quiz"):
        respuestas_usuario = []
        for i, pregunta in enumerate(st.session_state.quiz_preguntas):
            seleccion = st.radio(
                f"{i + 1}. {pregunta['pregunta']}",
                options=list(range(len(pregunta["opciones"]))),
                format_func=lambda idx, p=pregunta: p["opciones"][idx],
                key=f"quiz_pregunta_{i}",
                index=None,
            )
            respuestas_usuario.append(seleccion)

        enviado = st.form_submit_button("Enviar respuestas")

    if enviado:
        if any(r is None for r in respuestas_usuario):
            st.error("Responde las 3 preguntas antes de enviar.")
        else:
            resultado = evaluar_quiz(sesion, respuestas_usuario)
            if "error" in resultado:
                st.error(resultado["error"])
            else:
                _agregar_al_historial(
                    "user", "(Envié mis respuestas del quiz)"
                )
                _agregar_al_historial("assistant", resultado["mensaje"])
                if resultado["correctas"] == resultado["total"]:
                    st.balloons()
                st.session_state.quiz_preguntas = None
                st.session_state.quiz_meta = None
                st.rerun()

    if st.button("Cancelar quiz"):
        st.session_state.quiz_preguntas = None
        st.session_state.quiz_meta = None
        st.rerun()


# --------------------------------------------------------------------------
# Accesos rápidos a "ruta" y "quiz" una vez hay un tema activo
# --------------------------------------------------------------------------

if sesion.tema_actual and not sesion.esperando_consentimiento and st.session_state.quiz_preguntas is None:
    col_ruta, col_quiz = st.columns(2)
    with col_ruta:
        if st.button("🗺️ Ver ruta de aprendizaje", use_container_width=True):
            tema_activo = obtener_tema(sesion.tema_actual)
            pasos = "\n".join(f"{i + 1}. {paso}" for i, paso in enumerate(tema_activo["ruta_aprendizaje"]))
            _agregar_al_historial("user", "Muéstrame la ruta de aprendizaje")
            _agregar_al_historial(
                "assistant",
                f"Ruta breve para '{tema_activo['nombre_visible']}':\n\n{pasos}\n\n"
                f"Fuente: {tema_activo['fuente']}.",
            )
            st.rerun()
    with col_quiz:
        if st.button("📝 Hacer el quiz (3 preguntas)", use_container_width=True):
            resultado_quiz = iniciar_quiz(sesion)
            if "error" in resultado_quiz:
                st.error(resultado_quiz["error"])
            else:
                st.session_state.quiz_preguntas = resultado_quiz["preguntas"]
                st.session_state.quiz_meta = {
                    "nombre_visible": resultado_quiz["nombre_visible"],
                    "fuente": resultado_quiz["fuente"],
                }
                st.rerun()


# --------------------------------------------------------------------------
# Entrada de chat libre
# --------------------------------------------------------------------------

texto_usuario = st.chat_input("Escribe tu pregunta o el tema que te interesa...")

if texto_usuario:
    _agregar_al_historial("user", texto_usuario)

    texto_normalizado = texto_usuario.strip().lower()

    # Comandos rápidos por texto, equivalentes a los botones de arriba.
    if not sesion.esperando_consentimiento and sesion.tema_actual and texto_normalizado == "quiz":
        resultado_quiz = iniciar_quiz(sesion)
        if "error" in resultado_quiz:
            _agregar_al_historial("assistant", resultado_quiz["error"])
        else:
            st.session_state.quiz_preguntas = resultado_quiz["preguntas"]
            st.session_state.quiz_meta = {
                "nombre_visible": resultado_quiz["nombre_visible"],
                "fuente": resultado_quiz["fuente"],
            }
    elif not sesion.esperando_consentimiento and sesion.tema_actual and texto_normalizado == "ruta":
        tema_activo = obtener_tema(sesion.tema_actual)
        pasos = "\n".join(f"{i + 1}. {paso}" for i, paso in enumerate(tema_activo["ruta_aprendizaje"]))
        _agregar_al_historial(
            "assistant",
            f"Ruta breve para '{tema_activo['nombre_visible']}':\n\n{pasos}\n\n"
            f"Fuente: {tema_activo['fuente']}.",
        )
    else:
        resultado = procesar_mensaje(sesion, texto_usuario)
        _agregar_al_historial("assistant", resultado["respuesta"])

    st.rerun()

