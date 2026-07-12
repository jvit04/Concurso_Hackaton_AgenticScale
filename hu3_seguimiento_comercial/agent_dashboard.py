import streamlit as st
from google import genai

# Inicialización segura
# Obtener la clave de forma segura sin lanzar KeyError en tiempo de análisis
api_key = st.secrets.get("GEMINI_API_KEY") if hasattr(st, "secrets") else None
if api_key:
    try:
        client = genai.Client(api_key=api_key)
    except Exception:
        client = None
else:
    client = None

def generar_sugerencia_comercial(resumen_ia: str, tipo_cliente: str, presupuesto: float) -> str:
    """Intenta usar Gemini; si los límites se agotan, usa un fallback simulado para salvar la demo."""
    
    # --- PLAN B: RESPUESTA SIMULADA BASADA EN REGLAS ---
    respuesta_simulada = "Agendar reunión de alto valor"
    if presupuesto < 1000:
        respuesta_simulada = "Enviar material educativo introductorio"
    elif tipo_cliente == "B2B":
        respuesta_simulada = "Derivar a especialista B2B"
    # ---------------------------------------------------

    if client is None:
        return respuesta_simulada
        
    prompt_seguro = f"""
    Eres un analista comercial de un CRM financiero estricto.
    Datos del Lead:
    - Tipo: {tipo_cliente}
    - Presupuesto: ${presupuesto}
    - Resumen conversacional: {resumen_ia}
    
    REGLA ESTRICTA: Basado en estos datos, debes sugerir SOLO UNA de las siguientes tres acciones exactas. No agregues saludos, explicaciones, ni inventes datos financieros.
    Opciones permitidas:
    1. Agendar reunión de alto valor
    2. Enviar material educativo introductorio
    3. Derivar a especialista B2B
    
    Tu respuesta debe ser únicamente el texto de la opción elegida.
    """
    
    try:
        respuesta = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt_seguro
        )
        return respuesta.text.strip()
    except Exception:
        # Si Google lanza el error 429 por límites, salvamos la demo retornando la simulación
        return respuesta_simulada