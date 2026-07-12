# shared/ui_styles.py
import streamlit as st

def aplicar_estilos_globales():
    """Inyecta el CSS centralizado de ATLAS Financial AI."""
    st.markdown("""
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

        /* Tipografía general (sin afectar los iconos nativos) */
        .stApp, .stApp p, .stApp label {
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

        /* Eliminar DEFINITIVAMENTE el botón de colapsar sidebar (ícono roto).
        Cubre todas las variantes de nombre entre versiones de Streamlit. */
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"],
        [data-testid="baseButton-headerNoPadding"],
        button[kind="headerNoPadding"],
        .stSidebar button[kind="header"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            height: 0 !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }

        </style>
        """, unsafe_allow_html=True)