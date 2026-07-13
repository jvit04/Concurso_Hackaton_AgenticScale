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

from shared.ui_styles import aplicar_estilos_globales

#st.set_page_config(
#    page_title="Agente Comercial IA · HU1",
#    page_icon="💼",
#    layout="centered",
#    initial_sidebar_state="expanded",
#)

# Inyectar el diseño unificado
aplicar_estilos_globales()

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

    from hu1_calificacion_leads.agent_commercial import (
        RECHAZO_MONTO_ALTO, RECHAZO_MONTO_NEGATIVO, RECHAZO_EMAIL_INVALIDO,
    )
    mensajes_especificos = {
        RECHAZO_MONTO_ALTO: "Ese monto parece muy alto. ¿Podrías confirmarlo o "
                            "ingresar una cifra más ajustada?",
        RECHAZO_MONTO_NEGATIVO: "El monto debe ser un número positivo. ¿Podrías "
                                "ingresarlo de nuevo?",
        RECHAZO_EMAIL_INVALIDO: "Ese correo no parece válido. ¿Podrías escribirlo "
                                "de nuevo? (ejemplo: nombre@correo.com)",
    }
    if valor in mensajes_especificos:
        _agregar("assistant", mensajes_especificos[valor])
        return

    # Política de re-preguntar ante None (una vez)
    if valor is None:
        if st.session_state.reintentos == 0:
            st.session_state.reintentos += 1
            _agregar("assistant",
                     "🤔 No logré entender tu respuesta. ¿Podrías intentarlo de nuevo?")
            return
        else:
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
    saludo = "¡Gracias por tu tiempo! 🙌"

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

# ==========================================================================
# Auto-scroll al fondo
# ==========================================================================
st.html(
    """
    <script>
        const doc = window.parent.document;
        // 'auto' = salto instantáneo, no 'smooth'.
        function anclarAbajo() {
            const cont = doc.querySelector('[data-testid="stAppViewContainer"]');
            if (cont) cont.scrollTo({top: cont.scrollHeight, behavior: 'auto'});
            const main = doc.querySelector('section.main');
            if (main) main.scrollTo({top: main.scrollHeight, behavior: 'auto'});
        }
        let t0 = Date.now();
        function bucle() {
            anclarAbajo();
            if (Date.now() - t0 < 1500) requestAnimationFrame(bucle);
        }
        bucle();
    </script>
    """
)