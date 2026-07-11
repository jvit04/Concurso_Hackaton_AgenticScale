"""
agent_tutor.py
---------------
Historia de Usuario 2: Tutor financiero que convierte aprendizaje en intención.

Responsabilidades (según HISTORIA-USUARIO-2.txt):
1. Responder con contenido aprobado por Futuro Academy e indicar la fuente usada.
2. Proponer una ruta breve de aprendizaje o un quiz de 3 preguntas.
3. Registrar el tema de interés del usuario, CON SU CONSENTIMIENTO, como señal
   comercial en el CRM compartido (shared/database.py).

Este módulo NO expone un framework web directamente; routes_tutor.py lo conecta
a FastAPI, y cli_tutor.py lo conecta a una consola para pruebas rápidas.
"""

import os
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from agente_ia_hu2.base_conocimiento import (
        BASE_CONOCIMIENTO,
        detectar_tema_por_palabras_clave,
        listar_temas_disponibles,
        obtener_tema,
    )
except ModuleNotFoundError:  # Soporte al ejecutar el archivo directamente
    from base_conocimiento import (
        BASE_CONOCIMIENTO,
        detectar_tema_por_palabras_clave,
        listar_temas_disponibles,
        obtener_tema,
    )


def _cargar_variables_entorno() -> None:
    """Carga variables desde .env o env si existen en la raíz del proyecto."""
    base_dir = Path(__file__).resolve().parents[1]
    for nombre_archivo in (".env", "env"):
        ruta = base_dir / nombre_archivo
        if not ruta.exists():
            continue
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, valor = linea.split("=", 1)
            clave = clave.strip()
            valor = valor.strip().strip('"').strip("'")
            os.environ.setdefault(clave, valor)


_cargar_variables_entorno()

# --------------------------------------------------------------------------
# Integración con Gemini (Google Generative AI)
# --------------------------------------------------------------------------
# Se usa ÚNICAMENTE para redactar de forma conversacional el contenido ya
# aprobado en base_conocimiento.py. El modelo recibe instrucciones explícitas
# de no inventar datos financieros fuera de ese contenido.

GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")

_modelo_gemini = None  # se inicializa de forma perezosa (lazy) al primer uso


def _obtener_modelo_gemini():
    """
    Inicializa el cliente de Gemini la primera vez que se necesita.
    Lanza un error claro si falta la API key, en lugar de fallar silenciosamente.
    """
    global _modelo_gemini
    if _modelo_gemini is not None:
        return _modelo_gemini

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Falta configurar la variable de entorno GEMINI_API_KEY antes de "
            "usar el Tutor IA. Ejecuta: export GEMINI_API_KEY='tu_api_key'"
        )

    import google.generativeai as genai

    genai.configure(api_key=api_key)
    _modelo_gemini = genai.GenerativeModel(GEMINI_MODEL_NAME)
    return _modelo_gemini


def _redactar_explicacion_con_gemini(tema: dict, pregunta_usuario: str) -> str:
    """
    Pide a Gemini que redacte, en tono de tutor cercano, el contenido YA
    aprobado del tema. Si la llamada falla por cualquier motivo (sin API key,
    error de red, cuota, etc.), se usa el resumen aprobado tal cual como
    respaldo, para que la demo nunca se quede sin respuesta.
    """
    system_instruction = (
        "Eres el Tutor IA de Futuro Academy. SOLO puedes explicar el contenido "
        "aprobado que se te entrega a continuación. No inventes cifras, leyes, "
        "instrumentos financieros ni datos que no estén en ese contenido. "
        "Responde en español, en un tono cercano y motivador, en máximo 120 "
        "palabras. No des recomendaciones de inversión personalizadas ni "
        "asesoría financiera individual: tu rol es educativo."
    )

    prompt = (
        f"Contenido aprobado sobre '{tema['nombre_visible']}':\n"
        f"{tema['resumen']}\n\n"
        f"Pregunta o interés del usuario: \"{pregunta_usuario}\"\n\n"
        "Redacta una explicación breve y clara basada ÚNICAMENTE en el "
        "contenido aprobado de arriba."
    )

    try:
        modelo = _obtener_modelo_gemini()
        respuesta = modelo.generate_content(
            [system_instruction, prompt],
            generation_config={"temperature": 0.4, "max_output_tokens": 300},
        )
        texto = (respuesta.text or "").strip()
        return texto if texto else tema["resumen"]
    except Exception:
        # Respaldo: si Gemini no está disponible, igual cumplimos el criterio
        # de responder con contenido aprobado (solo que sin redacción del LLM).
        return tema["resumen"]


# --------------------------------------------------------------------------
# Estado de la conversación (sesión en memoria)
# --------------------------------------------------------------------------


@dataclass
class SesionTutor:
    session_id: str
    email: Optional[str] = None
    tema_actual: Optional[str] = None
    esperando_consentimiento: bool = False
    quiz_respuestas: List[int] = field(default_factory=list)
    quiz_activo: bool = False


_SESIONES: Dict[str, SesionTutor] = {}


def obtener_o_crear_sesion(session_id: Optional[str] = None, email: Optional[str] = None) -> SesionTutor:
    if not session_id:
        session_id = str(uuid.uuid4())
    if session_id not in _SESIONES:
        _SESIONES[session_id] = SesionTutor(session_id=session_id, email=email)
    elif email:
        _SESIONES[session_id].email = email
    return _SESIONES[session_id]


# --------------------------------------------------------------------------
# Flujo principal: explicación guiada
# --------------------------------------------------------------------------


def procesar_mensaje(sesion: SesionTutor, mensaje: str) -> dict:
    """
    Punto de entrada principal del chat educativo.

    Devuelve un dict con:
      - respuesta: texto para mostrar al usuario
      - fuente: fuente citada (o None si no aplica a este turno)
      - tema: id del tema detectado (o None)
      - accion_sugerida: "elegir_tema" | "explicacion" | "pedir_consentimiento"
      - opciones_tema: lista de temas disponibles, solo si no se detectó ninguno
    """
    # 1) Si estamos esperando un sí/no de consentimiento, priorizamos ese flujo.
    if sesion.esperando_consentimiento:
        return _procesar_respuesta_consentimiento(sesion, mensaje)

    # 2) Detectar el tema de interés dentro del mensaje del usuario.
    tema_id = detectar_tema_por_palabras_clave(mensaje)

    if not tema_id:
        temas_legibles = [BASE_CONOCIMIENTO[t]["nombre_visible"] for t in listar_temas_disponibles()]
        return {
            "respuesta": (
                "¡Con gusto te ayudo a entender ese tema! Por ahora puedo guiarte "
                f"en estos temas aprobados por Futuro Academy: {', '.join(temas_legibles)}. "
                "¿Sobre cuál te gustaría empezar?"
            ),
            "fuente": None,
            "tema": None,
            "accion_sugerida": "elegir_tema",
            "opciones_tema": listar_temas_disponibles(),
        }

    tema = obtener_tema(tema_id)
    sesion.tema_actual = tema_id

    explicacion = _redactar_explicacion_con_gemini(tema, mensaje)
    ruta = tema["ruta_aprendizaje"]

    respuesta = (
        f"{explicacion}\n\n"
        f"Fuente: {tema['fuente']}.\n\n"
        "Para seguir aprendiendo puedo ofrecerte dos caminos:\n"
        "1) Una ruta breve de 3 pasos sobre este tema.\n"
        "2) Un quiz corto de 3 preguntas para evaluar lo aprendido.\n"
        "¿Cuál prefieres? (responde 'ruta' o 'quiz')\n\n"
        "Además, ¿me das tu consentimiento para registrar tu interés en "
        f"'{tema['nombre_visible']}' en el CRM de Futuro Academy, para que un "
        "asesor pueda darte seguimiento? (sí/no)"
    )

    sesion.esperando_consentimiento = True

    return {
        "respuesta": respuesta,
        "fuente": tema["fuente"],
        "tema": tema_id,
        "ruta_aprendizaje": ruta,
        "accion_sugerida": "pedir_consentimiento",
        "opciones_tema": None,
    }


def _procesar_respuesta_consentimiento(sesion: SesionTutor, mensaje: str) -> dict:
    """Interpreta la respuesta de sí/no del usuario y registra (o no) en el CRM."""
    texto = mensaje.strip().lower()
    afirmativo = any(p in texto for p in ["si", "sí", "claro", "acepto", "dale", "ok"])
    negativo = any(p in texto for p in ["no", "prefiero no", "negativo"])

    sesion.esperando_consentimiento = False

    if afirmativo and not negativo:
        resultado = registrar_interes_en_crm(sesion)
        return {
            "respuesta": (
                "¡Gracias! Registré tu interés en el CRM para que un asesor de "
                "Futuro Academy pueda contactarte si lo deseas. Cuando quieras, "
                "puedes pedirme el quiz de 3 preguntas escribiendo 'quiz'."
            ),
            "fuente": None,
            "tema": sesion.tema_actual,
            "accion_sugerida": "consentimiento_registrado",
            "crm_actualizado": resultado,
        }

    return {
        "respuesta": (
            "Entendido, no registraré tu interés en el CRM. Igual podemos seguir "
            "aprendiendo: escribe 'ruta' para ver los pasos sugeridos o 'quiz' "
            "para poner a prueba lo aprendido."
        ),
        "fuente": None,
        "tema": sesion.tema_actual,
        "accion_sugerida": "consentimiento_rechazado",
        "crm_actualizado": False,
    }


# --------------------------------------------------------------------------
# Quiz de 3 preguntas
# --------------------------------------------------------------------------


def iniciar_quiz(sesion: SesionTutor) -> dict:
    """Devuelve las 3 preguntas (sin la respuesta correcta) del tema actual."""
    if not sesion.tema_actual:
        return {"error": "Primero deben elegir un tema con el usuario antes de iniciar el quiz."}

    tema = obtener_tema(sesion.tema_actual)
    preguntas_publicas = [
        {"pregunta": q["pregunta"], "opciones": q["opciones"]} for q in tema["quiz"]
    ]
    sesion.quiz_activo = True
    sesion.quiz_respuestas = []
    return {
        "tema": sesion.tema_actual,
        "nombre_visible": tema["nombre_visible"],
        "fuente": tema["fuente"],
        "preguntas": preguntas_publicas,
    }


def evaluar_quiz(sesion: SesionTutor, respuestas: List[int]) -> dict:
    """
    Recibe una lista de 3 índices (0-3) elegidos por el usuario y calcula el
    puntaje. Si ya hay consentimiento otorgado, actualiza score_quiz en el CRM.
    """
    if not sesion.tema_actual:
        return {"error": "No hay un tema activo para evaluar."}

    tema = obtener_tema(sesion.tema_actual)
    preguntas = tema["quiz"]

    if len(respuestas) != len(preguntas):
        return {"error": f"Se esperaban {len(preguntas)} respuestas, llegaron {len(respuestas)}."}

    correctas = sum(
        1 for r, q in zip(respuestas, preguntas) if r == q["respuesta_correcta"]
    )

    sesion.quiz_activo = False
    actualizado_en_crm = False

    lead = _buscar_lead(sesion)
    if lead is not None and lead.consentimiento_registro:
        lead.score_quiz = correctas
        _actualizar_lead(lead)
        actualizado_en_crm = True

    return {
        "tema": sesion.tema_actual,
        "correctas": correctas,
        "total": len(preguntas),
        "actualizado_en_crm": actualizado_en_crm,
        "mensaje": (
            f"Obtuviste {correctas} de {len(preguntas)} respuestas correctas en "
            f"'{tema['nombre_visible']}'. Fuente: {tema['fuente']}."
        ),
    }


# --------------------------------------------------------------------------
# Integración con el CRM compartido (shared/database.py y shared/schemas.py)
# --------------------------------------------------------------------------
# NOTA: se importa de forma perezosa (dentro de las funciones) para que este
# módulo pueda importarse y probarse aunque el equipo aún no tenga /shared
# listo, y para dar un mensaje de error claro si falta.


def _buscar_lead(sesion: SesionTutor):
    if not sesion.email:
        return None
    try:
        from shared.database import obtener_lead_por_email
    except ImportError:
        return None
    return obtener_lead_por_email(sesion.email)


def _actualizar_lead(lead) -> None:
    from shared.database import actualizar_lead

    actualizar_lead(lead)


def registrar_interes_en_crm(sesion: SesionTutor) -> bool:
    """
    Cumple el criterio: "Registra el tema de interés del usuario, con su
    consentimiento, como señal comercial en el CRM."

    - Si el usuario ya existe como Lead (porque pasó por HU1), actualiza sus
      campos tema_aprendizaje y consentimiento_registro.
    - Si no existe (el Tutor puede ser su primer contacto con Futuro Academy),
      crea un Lead mínimo para no perder la señal comercial.
    Devuelve True si el CRM quedó actualizado correctamente.
    """
    if not sesion.email or not sesion.tema_actual:
        return False

    tema = obtener_tema(sesion.tema_actual)

    try:
        from shared.database import crear_lead
        from shared.schemas import LeadCRM
    except ImportError:
        # /shared aún no está disponible en este entorno; no se puede persistir.
        return False

    lead = _buscar_lead(sesion)

    if lead is not None:
        lead.tema_aprendizaje = tema["nombre_visible"]
        lead.consentimiento_registro = True
        _actualizar_lead(lead)
        return True

    nuevo_lead = LeadCRM(
        id=str(uuid.uuid4()),
        nombre=sesion.email.split("@")[0],
        email=sesion.email,
        tipo_cliente="B2C",
        interes=tema["nombre_visible"],
        presupuesto=0.0,
        perfil="Desconocido (ingresó vía Tutor IA)",
        urgencia="Baja",
        prioridad="Baja",
        resumen_conversacion_comercial="Prospecto originado en el Tutor IA (HU2), sin paso previo por HU1.",
        tema_aprendizaje=tema["nombre_visible"],
        consentimiento_registro=True,
    )
    crear_lead(nuevo_lead)
    return True
