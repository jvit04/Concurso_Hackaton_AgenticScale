"""
streamlit_app.py — HU1 · Agente Comercial IA (Calificación de leads)
====================================================================
Chat guiado que orquesta el flujo completo de calificación:
    apertura -> clasificación (B2B/B2C) -> rama específica -> cierre
y al finalizar calcula la prioridad, genera el resumen y persiste el
lead en el CRM compartido (vía agent_commercial.guardar_lead).

No modifica agent_commercial.py: solo lo consume. El router FastAPI y
cualquier otro canal siguen funcionando igual.

Cómo correrlo (desde la raíz del proyecto):
    streamlit run hu1_calificacion_leads/streamlit_app.py

Sigue el mismo patrón de estado que la UI de HU2: como Streamlit re-ejecuta
el script en cada interacción, todo el estado conversacional vive en
st.session_state.
"""

import os
import sys
import time
import random
import html
import streamlit.components.v1 as components
from pathlib import Path

# Asegurar que la raíz del proyecto esté en sys.path, para importar
# 'hu1_calificacion_leads' y 'shared' sin importar el cwd de ejecución.
_RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, _RAIZ_PROYECTO)

import streamlit as st

try:
    from hu1_calificacion_leads.agent_commercial import (
        PREGUNTAS_COMUNES_APERTURA, PREGUNTA_CLASIFICACION,
        PREGUNTAS_COMUNES_CIERRE, PREGUNTAS,
        interpretar_respuesta, ensamblar_datos, guardar_lead,
    )
except ModuleNotFoundError:  # ejecución directa desde la carpeta del módulo
    from agent_commercial import (
        PREGUNTAS_COMUNES_APERTURA, PREGUNTA_CLASIFICACION,
        PREGUNTAS_COMUNES_CIERRE, PREGUNTAS,
        interpretar_respuesta, ensamblar_datos, guardar_lead,
    )

st.set_page_config(
    page_title="Agente Comercial IA · HU1",
    page_icon="💼",
    layout="centered",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# Estilo visual (alineado con la UI de HU2 para consistencia en la demo)
# --------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined');

    :root {
        --acento: #6366f1;
        --acento-dark: #4f46e5;
        --acento-soft: #eef2ff;
        --texto: #1e1b2e;
        --texto-muted: #6b7280;
        --burbuja-bot: #ffffff;
        --burbuja-user: #6366f1;
    }

    /* Fondo con gradiente suave */
    .stApp {
        background: linear-gradient(160deg, #f5f3ff 0%, #eef2ff 40%, #faf5ff 100%);
        font-family: 'Inter', sans-serif;
        color: var(--texto);
    }

    /* Tipografía general */
    .stApp, .stApp p, .stApp div, .stApp span, .stApp label {
        font-family: 'Inter', sans-serif;
        color: var(--texto);
    }

    /* Títulos con más carácter */
    h1 {
        font-weight: 700 !important;
        letter-spacing: -0.02em;
        background: linear-gradient(120deg, var(--acento-dark), #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* Sidebar OSCURO (contraste tipo Notion/Linear) */
    .stSidebar {
        background: linear-gradient(180deg, #1e1b3a 0%, #2d2456 100%) !important;
        border-right: 1px solid rgba(99,102,241,0.25);
    }
    /* Texto claro dentro del sidebar oscuro */
    .stSidebar, .stSidebar * {
        color: #e5e7ff !important;
    }
    .stSidebar .stCaption, .stSidebar [data-testid="stCaptionContainer"] {
        color: #a5a3c9 !important;
    }
    /* El warning/success del sidebar, más integrados al fondo oscuro */
    .stSidebar .stAlert {
        background: rgba(139,92,246,0.12) !important;
        border: 1px solid rgba(139,92,246,0.25) !important;
        border-radius: 14px !important;
        box-shadow: none !important;
    }
    .stSidebar .stAlert * {
        color: #c7c3f0 !important;
        font-size: 0.82rem !important;
    }

    /* Ocultar la barra superior default de Streamlit (Deploy, menú) */
    header[data-testid="stHeader"] {
        display: none !important;
    }

    /* Botones: índigo con sombra y hover elevado */
    .stButton > button {
        background: var(--acento);
        color: #ffffff !important;
        border-radius: 12px;
        border: none;
        font-weight: 600;
        padding: 0.55rem 1rem;
        box-shadow: 0 4px 14px rgba(99,102,241,0.35);
        transition: all 0.18s ease;
    }
    .stButton > button:hover {
        background: var(--acento-dark);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(99,102,241,0.45);
    }
    .stButton > button * { color: #ffffff !important; }

    /* Input de chat redondeado */
    .stChatInput textarea, .stTextInput > div > div > input {
        border-radius: 14px !important;
        border: 1.5px solid rgba(99,102,241,0.25) !important;
        background: #ffffff !important;
        color: var(--texto) !important;
    }
    .stChatInput textarea:focus {
        border-color: var(--acento) !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
    }

    /* Ocultar el avatar default de st.chat_message (usamos burbujas propias) */
    [data-testid="stChatMessageAvatarUser"],
    [data-testid="stChatMessageAvatarAssistant"] { display: none; }

    /* Burbujas de chat estilo iMessage */
    .burbuja-fila { display: flex; margin: 6px 0; }
    .burbuja-fila.bot { justify-content: flex-start; }
    .burbuja-fila.user { justify-content: flex-end; }
    .burbuja {
        max-width: 76%;
        padding: 12px 16px;
        border-radius: 20px;
        font-size: 0.97rem;
        line-height: 1.45;
        box-shadow: 0 2px 10px rgba(30,27,46,0.06);
        animation: aparecer 0.25s ease;
    }
    .burbuja.bot {
        background: var(--burbuja-bot);
        color: var(--texto) !important;
        border-bottom-left-radius: 6px;
    }
    .burbuja.user {
        background: var(--burbuja-user);
        color: #ffffff !important;
        border-bottom-right-radius: 6px;
    }
    .burbuja.user * { color: #ffffff !important; }
    @keyframes aparecer {
        from { opacity: 0; transform: translateY(6px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* Success box (mensaje de cierre) más suave */
    .stSuccess { border-radius: 16px; }

    /* ============ CHAT INPUT — marco flotante blanco, sin doble borde ============ */

    /* Contenedor exterior: transparente, sin borde ni tinte (mata el azul de focus) */
    [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* El marco flotante REAL: una sola tarjeta blanca redondeada */
    [data-testid="stChatInput"] {
        background: #ffffff !important;
        border: 1.5px solid rgba(99,102,241,0.20) !important;
        border-radius: 18px !important;
        box-shadow: 0 6px 24px rgba(30,27,46,0.10) !important;
        padding: 4px 6px !important;
    }
    /* Al enfocar: solo un halo suave índigo, sin cambiar el borde a azul fuerte */
    [data-testid="stChatInput"]:focus-within {
        border-color: rgba(99,102,241,0.35) !important;
        box-shadow: 0 6px 24px rgba(99,102,241,0.18) !important;
    }

    /* El textarea interior: SIN borde propio (elimina el marco doble) */
    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInputContainer"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }

    /* Botón de enviar en índigo */
    [data-testid="stChatInput"] button {
        background: var(--acento) !important;
        border-radius: 12px !important;
    }
    [data-testid="stChatInput"] button:hover {
        background: var(--acento-dark) !important;
    }

    
    /* --- CAMBIO 3: Indicador "escribiendo..." con tres puntos --- */
    .typing-burbuja {
        display: inline-flex; gap: 5px; align-items: center;
        background: var(--burbuja-bot);
        padding: 14px 18px; border-radius: 20px;
        border-bottom-left-radius: 6px;
        box-shadow: 0 2px 10px rgba(30,27,46,0.06);
    }
    .typing-dot {
        width: 8px; height: 8px; border-radius: 50%;
        background: var(--acento);
        animation: typing 1.2s infinite ease-in-out;
    }
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes typing {
        0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
        30% { transform: translateY(-6px); opacity: 1; }
    }

    [data-testid="stChatInput"] textarea:focus,
    [data-testid="stChatInput"] textarea:focus-visible,
    [data-testid="stChatInput"] textarea:active {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }

    /* Franja de marca superior — texto plomo, ancho completo del chat */
    .topbar-marca {
        width: 100%;
        font-size: 0.82rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #9ca3af !important;
        padding-bottom: 10px;
        margin-bottom: 18px;
        border-bottom: 1px solid rgba(156,163,175,0.20);
    }

    /* Forzar sidebar SIEMPRE visible y expandido (sin depender del botón roto) */
    [data-testid="stSidebar"] {
        display: flex !important;
        visibility: visible !important;
        transform: none !important;
        min-width: 300px !important;
        width: 300px !important;
        height: 100vh !important;
        overflow: hidden !important;
    }
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"] {
        display: flex !important;
        flex-direction: column !important;
        height: 100% !important;
        overflow: hidden !important;
    }
    .sb-footer {
        margin-top: auto !important;
        padding-top: 16px;
    }
    
/* ===================== SIDEBAR — contenido ===================== */

    /* 1. Encabezado tipo perfil */
    .sb-header {
        display: flex; align-items: center; gap: 12px;
        padding: 4px 0 18px 0;
        border-bottom: 1px solid rgba(255,255,255,0.10);
        margin-bottom: 20px;
    }
    .sb-avatar {
        width: 42px; height: 42px; border-radius: 12px;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        display: flex; align-items: center; justify-content: center;
        font-size: 1.3rem; font-weight: 700; color: #fff !important;
        box-shadow: 0 4px 12px rgba(99,102,241,0.4);
    }
    .sb-title { font-size: 1rem; font-weight: 700; color: #f0eeff !important; }
    .sb-sub   { font-size: 0.75rem; color: #9d99c9 !important; }

    /* 2. Progreso */
    .sb-progress-label {
        font-size: 0.72rem; font-weight: 600; letter-spacing: 0.08em;
        text-transform: uppercase; color: #8b88b8 !important;
        margin-bottom: 12px;
    }
    .sb-steps { display: flex; flex-direction: column; gap: 4px; margin-bottom: 24px; }
    .sb-step {
        display: flex; align-items: center; gap: 11px;
        padding: 9px 12px; border-radius: 10px;
        font-size: 0.88rem; transition: all 0.2s ease;
    }
    .sb-step-ico { font-size: 0.9rem; width: 16px; text-align: center; }
    .sb-step.done .sb-step-ico  { color: #34d399 !important; }
    .sb-step.done .sb-step-txt  { color: #b8b5da !important; }
    .sb-step.active {
        background: rgba(99,102,241,0.20);
        border: 1px solid rgba(99,102,241,0.35);
    }
    .sb-step.active .sb-step-ico { color: #a5b4fc !important; }
    .sb-step.active .sb-step-txt { color: #ffffff !important; font-weight: 600; }
    .sb-step.pending .sb-step-ico { color: #56537a !important; }
    .sb-step.pending .sb-step-txt { color: #6f6c94 !important; }

    /* Nota de estado (Gemini) */
    .sb-note {
        font-size: 0.75rem; line-height: 1.4;
        color: #9d99c9 !important;
        background: rgba(139,92,246,0.10);
        border: 1px solid rgba(139,92,246,0.18);
        border-radius: 10px; padding: 10px 12px; margin-bottom: 16px;
    }

    /* 3. Footer */
    .sb-footer {
        margin-top: 28px; padding-top: 16px;
        border-top: 1px solid rgba(255,255,255,0.08);
        font-size: 0.72rem; color: #6f6c94 !important; text-align: center;
    }
    .sb-footer b { color: #9d99c9 !important; }



    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Barra superior propia (reemplaza la de Streamlit, oculta por CSS)
# --------------------------------------------------------------------------
st.markdown(
    """
    <div class="topbar-marca">Atlas Financial AI</div>
    """,
    unsafe_allow_html=True,
)

# Estados del flujo (máquina de estados de la conversación)
APERTURA, CLASIFICACION, RAMA, CIERRE, FINALIZADO = (
    "apertura", "clasificacion", "rama", "cierre", "finalizado"
)


# --------------------------------------------------------------------------
# Estado de la sesión
# --------------------------------------------------------------------------
def _inicializar_estado():
    defaults = {
        "estado": APERTURA,
        "idx": 0,
        "tipo_cliente": None,
        "respuestas": [],        # lista de (pregunta_dict, valor)
        "reintentos": 0,
        "historial": [],         # [{"role":..., "content":...}] solo para pintar
        "lead": None,            # LeadCRM resultante
        "arrancado": False,      # ya mostramos la primera pregunta?
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _reiniciar():
    for k in ["estado", "idx", "tipo_cliente", "respuestas",
              "reintentos", "historial", "lead", "arrancado"]:
        st.session_state.pop(k, None)
    _inicializar_estado()


def _lista_actual():
    e = st.session_state.estado
    if e == APERTURA:      return PREGUNTAS_COMUNES_APERTURA
    if e == CLASIFICACION: return [PREGUNTA_CLASIFICACION]
    if e == RAMA:          return PREGUNTAS.get(st.session_state.tipo_cliente, [])
    if e == CIERRE:        return PREGUNTAS_COMUNES_CIERRE
    return []


def _pregunta_actual():
    lista = _lista_actual()
    if st.session_state.idx < len(lista):
        return lista[st.session_state.idx]
    return None


def _avanzar_estado():
    e = st.session_state.estado
    st.session_state.estado = {
        APERTURA: CLASIFICACION, CLASIFICACION: RAMA,
        RAMA: CIERRE, CIERRE: FINALIZADO,
    }.get(e, FINALIZADO)
    st.session_state.idx = 0


def _agregar(role, content):
    st.session_state.historial.append({"role": role, "content": content})
    if role == "assistant":
        st.session_state.animar_ultimo = True   # el próximo render anima este mensaje

def _stream_texto(texto: str):
    """Generador para st.write_stream: emite el texto en fragmentos pequeños
    (no palabra completa) con pausas variables, simulando tipeo humano.
    Pausa más larga después de puntuación para que se sienta natural."""
    i = 0
    n = len(texto)
    while i < n:
        # fragmento de 2 a 4 caracteres por "tecleo"
        salto = random.randint(2, 4)
        fragmento = texto[i:i + salto]
        yield fragmento
        i += salto
        # pausa base + variación aleatoria (tipeo humano no es constante)
        pausa = random.uniform(0.02, 0.045)
        # pausa extra después de puntuación, como si "pensara" la frase
        if fragmento and fragmento[-1] in ".,!?":
            pausa += 0.25
        time.sleep(pausa)


def _finalizar():
    """Ensambla datos, refleja tolerancia en perfil (B2C), guarda el lead."""
    datos = ensamblar_datos(st.session_state.respuestas)
    # Enriquecer perfil de B2C con la tolerancia (evita perfil vacío en dashboard)
    if not datos.get("perfil") and datos.get("tolerancia_riesgo"):
        datos["perfil"] = f"Perfil de riesgo {datos['tolerancia_riesgo'].lower()}."
    lead = guardar_lead(datos)
    st.session_state.lead = lead
    return lead


def _procesar(texto_usuario):
    """Procesa la respuesta a la pregunta actual y avanza el flujo."""
    pregunta = _pregunta_actual()
    if pregunta is None:
        return

    valor = interpretar_respuesta(pregunta, texto_usuario)

    # Política de re-preguntar ante None (una vez)
    if valor is None:
        if st.session_state.reintentos == 0:
            st.session_state.reintentos += 1
            _agregar("assistant",
                     "🤔 No logré entender tu respuesta. ¿Podrías intentarlo de nuevo?")
            return
        else:
            # segundo fallo: se omite el dato y se avanza
            st.session_state.reintentos = 0
            st.session_state.respuestas.append((pregunta, None))
    else:
        st.session_state.reintentos = 0
        st.session_state.respuestas.append((pregunta, valor))
        if pregunta["id"] == PREGUNTA_CLASIFICACION["id"]:
            st.session_state.tipo_cliente = valor

    # avanzar índice / estado
    st.session_state.idx += 1
    while _pregunta_actual() is None and st.session_state.estado != FINALIZADO:
        _avanzar_estado()

    if st.session_state.estado == FINALIZADO:
        _finalizar()


_inicializar_estado()


# --------------------------------------------------------------------------
# Barra lateral: estado de Gemini + reinicio
# --------------------------------------------------------------------------
with st.sidebar:
    # --- 1. Encabezado tipo perfil de producto ---
    st.markdown(
        """
        <div class="sb-header">
            <div class="sb-avatar">A</div>
            <div class="sb-header-txt">
                <div class="sb-title">Agente Comercial IA</div>
                <div class="sb-sub">CRM · Chatbot</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- 2. Progreso de la conversación (basado en la máquina de estados) ---
    etapas = [
        ("Datos básicos", APERTURA),
        ("Clasificación", CLASIFICACION),
        ("Detalles", RAMA),
        ("Contacto", CIERRE),
    ]
    orden = {APERTURA: 0, CLASIFICACION: 1, RAMA: 2, CIERRE: 3, FINALIZADO: 4}
    actual = orden.get(st.session_state.estado, 0)

    filas = ""
    for nombre, estado_etapa in etapas:
        pos = orden[estado_etapa]
        if pos < actual:
            clase, icono = "done", "✓"
        elif pos == actual:
            clase, icono = "active", "●"
        else:
            clase, icono = "pending", "○"
        filas += (
            f'<div class="sb-step {clase}">'
            f'<span class="sb-step-ico">{icono}</span>'
            f'<span class="sb-step-txt">{nombre}</span></div>'
        )

    st.markdown(
        f'<div class="sb-progress-label">Progreso</div>'
        f'<div class="sb-steps">{filas}</div>',
        unsafe_allow_html=True,
    )

    # --- Aviso de estado de Gemini (discreto) ---
    if not os.getenv("GEMINI_API_KEY"):
        st.markdown(
            '<div class="sb-note">Modo sin conexión a Gemini · el resumen '
            'usa plantilla determinista.</div>',
            unsafe_allow_html=True,
        )

    # --- Botón de reinicio ---
    if st.button("Nueva conversación", use_container_width=True):
        _reiniciar()
        st.rerun()

    # --- 3. Footer ---
    st.markdown(
        '<div class="sb-footer">Powered by <b>Atlas Financial AI</b> · v1.0</div>',
        unsafe_allow_html=True,
    )

# --------------------------------------------------------------------------
# Encabezado
# --------------------------------------------------------------------------
st.title("💼 Agente Comercial IA")
st.caption("Conversa con el agente: te haremos algunas preguntas para "
           "calificar tu necesidad y dirigirte al asesor correcto.")

# Primera pregunta (al arrancar)
if not st.session_state.arrancado:
    primera = _pregunta_actual()
    if primera:
        _agregar("assistant", primera["texto"])
    st.session_state.arrancado = True


# --------------------------------------------------------------------------
# Historial de chat
# --------------------------------------------------------------------------
def _pintar_burbuja(role, contenido):
    """Pinta una burbuja estática (historial ya visto). El contenido se
    escapa siempre: aunque los mensajes del bot son de confianza (los
    escribimos nosotros), escapar parejo evita casos donde el bot repite
    texto del usuario (p. ej. en preguntas de opción)."""
    lado = "user" if role == "user" else "bot"
    seguro = html.escape(contenido)
    st.markdown(
        f'<div class="burbuja-fila {lado}"><div class="burbuja {lado}">{seguro}</div></div>',
        unsafe_allow_html=True,
    )


for i, turno in enumerate(st.session_state.historial):
    es_ultimo_bot = (
        i == len(st.session_state.historial) - 1
        and turno["role"] == "assistant"
        and st.session_state.get("animar_ultimo", False)
    )
    if es_ultimo_bot:
        placeholder = st.empty()
        # 1) Mostrar "escribiendo..." con puntos animados (más tiempo)
        placeholder.markdown(
            '<div class="burbuja-fila bot"><div class="typing-burbuja">'
            '<span class="typing-dot"></span><span class="typing-dot"></span>'
            '<span class="typing-dot"></span></div></div>',
            unsafe_allow_html=True,
        )
        time.sleep(random.uniform(1.2, 1.8))   # tiempo de "pensando" (más largo)
        # 2) Escribir el mensaje con typewriter
        acumulado = ""
        for fragmento in _stream_texto(turno["content"]):
            acumulado += fragmento
            seguro = html.escape(acumulado)
            placeholder.markdown(
                f'<div class="burbuja-fila bot"><div class="burbuja bot">{seguro}</div></div>',
                unsafe_allow_html=True,
            )
        st.session_state.animar_ultimo = False
    else:
        _pintar_burbuja(turno["role"], turno["content"])


# Pantalla final: lead guardado
# --------------------------------------------------------------------------
if st.session_state.estado == FINALIZADO and st.session_state.lead:
    lead = st.session_state.lead
    primer_nombre = (lead.nombre or "").split(" ")[0] if lead.nombre else ""
    # Limpiar caracteres de Markdown para que un nombre "raro" no rompa el formato
    primer_nombre = "".join(c for c in primer_nombre if c not in "*_`#[]()<>")
    saludo = f"¡Gracias por tu tiempo, {primer_nombre}! 🙌" if primer_nombre else "¡Gracias por tu tiempo! 🙌"

    st.success(
        f"{saludo}\n\n"
        "Ya registré tu información. Un asesor especializado revisará tu caso "
        "y se pondrá en contacto contigo pronto al correo que nos diste. "
        "¡Que tengas un excelente día!"
    )

    if st.button("➕ Iniciar una nueva conversación", use_container_width=True):
        _reiniciar()
        st.rerun()

# --------------------------------------------------------------------------
# Interacción activa: botones (opción) o texto libre
# --------------------------------------------------------------------------
else:
    pregunta = _pregunta_actual()
    if pregunta is not None:
        # Preguntas de opción -> botones; resto -> chat_input
        if pregunta["tipo"] == "opcion":
            st.markdown("<div style='height: 18px'></div>", unsafe_allow_html=True)
            # Etiquetas visibles = las claves "canónicas" del dict de opciones.
            vistas = {}
            for etiqueta, valor in pregunta["opciones"].items():
                vistas.setdefault(valor, etiqueta)
            cols = st.columns(len(vistas))
            for i, (valor, etiqueta) in enumerate(vistas.items()):
                with cols[i]:
                    if st.button(etiqueta.capitalize(), use_container_width=True,
                                 key=f"opt_{st.session_state.idx}_{valor}"):
                        _agregar("user", etiqueta)
                        _procesar(etiqueta)
                        # mostrar siguiente pregunta si no finalizó
                        sig = _pregunta_actual()
                        if sig and st.session_state.estado != FINALIZADO:
                            _agregar("assistant", sig["texto"])
                        st.rerun()
        else:
            texto = st.chat_input("Escribe tu respuesta...")
            if texto:
                _agregar("user", texto)
                _procesar(texto)
                sig = _pregunta_actual()
                if sig and st.session_state.estado != FINALIZADO:
                    _agregar("assistant", sig["texto"])
                st.rerun()

# ==========================================================================
# Auto-scroll al fondo — DEBE ser lo último del script, para correr cuando
# todo el contenido (burbujas, botones, cierre) ya está renderizado.
# ==========================================================================
components.html(
    """
    <script>
        const doc = window.parent.document;
        // 'auto' = salto instantáneo, no 'smooth'. Elimina el efecto de "viaje" visible.
        function anclarAbajo() {
            const cont = doc.querySelector('[data-testid="stAppViewContainer"]');
            if (cont) cont.scrollTo({top: cont.scrollHeight, behavior: 'auto'});
            const main = doc.querySelector('section.main');
            if (main) main.scrollTo({top: main.scrollHeight, behavior: 'auto'});
        }
        // Anclar de inmediato y repetir en cada frame durante ~1.5s,
        // para "pegar" la vista abajo mientras el contenido se monta.
        let t0 = Date.now();
        function bucle() {
            anclarAbajo();
            if (Date.now() - t0 < 1500) requestAnimationFrame(bucle);
        }
        bucle();
    </script>
    """,
    height=0,
)

components.html(
    """
    <script>
        const doc = window.parent.document;
        // 'auto' = salto instantáneo, no 'smooth'. Elimina el efecto de "viaje" visible.
        function anclarAbajo() {
            const cont = doc.querySelector('[data-testid="stAppViewContainer"]');
            if (cont) cont.scrollTo({top: cont.scrollHeight, behavior: 'auto'});
            const main = doc.querySelector('section.main');
            if (main) main.scrollTo({top: main.scrollHeight, behavior: 'auto'});
        }
        // Anclar de inmediato y repetir en cada frame durante ~1.5s,
        // para "pegar" la vista abajo mientras el contenido se monta.
        let t0 = Date.now();
        function bucle() {
            anclarAbajo();
            if (Date.now() - t0 < 1500) requestAnimationFrame(bucle);
        }
        bucle();
    </script>
    """,
    height=0,
)