"""
routes_tutor.py
-----------------
Endpoints REST del Tutor IA (HU2), pensados para montarse dentro del monolito
modular del equipo (main.py) junto a las rutas de HU1 y HU3.

Integración sugerida en main.py del equipo:

    from fastapi import FastAPI
    from hu2_tutor_financiero.routes_tutor import router as tutor_router

    app = FastAPI()
    app.include_router(tutor_router)
"""

import sys
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from agente_ia_hu2.agent_tutor import (
        evaluar_quiz,
        iniciar_quiz,
        obtener_o_crear_sesion,
        procesar_mensaje,
    )
except ModuleNotFoundError:  # Soporte al ejecutar el archivo directamente
    from agent_tutor import (
        evaluar_quiz,
        iniciar_quiz,
        obtener_o_crear_sesion,
        procesar_mensaje,
    )

router = APIRouter(prefix="/tutor", tags=["Tutor IA - HU2"])


# --------------------------------------------------------------------------
# Esquemas de entrada/salida de este router (independientes de shared/schemas.py,
# que modela el Lead del CRM, no la conversación).
# --------------------------------------------------------------------------


class MensajeEntrada(BaseModel):
    session_id: Optional[str] = None
    email: Optional[str] = None
    mensaje: str


class RespuestasQuizEntrada(BaseModel):
    session_id: str
    respuestas: List[int]


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------


@router.post("/mensaje")
def enviar_mensaje(payload: MensajeEntrada):
    """
    Punto de entrada conversacional principal. Detecta el tema, responde con
    contenido aprobado + fuente, ofrece ruta/quiz y gestiona el consentimiento.
    """
    sesion = obtener_o_crear_sesion(payload.session_id, payload.email)
    resultado = procesar_mensaje(sesion, payload.mensaje)
    resultado["session_id"] = sesion.session_id
    return resultado


@router.post("/quiz/iniciar")
def iniciar_quiz_endpoint(session_id: str):
    """Devuelve las 3 preguntas del tema actual de la sesión (sin respuestas)."""
    sesion = obtener_o_crear_sesion(session_id)
    resultado = iniciar_quiz(sesion)
    if "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])
    return resultado


@router.post("/quiz/responder")
def responder_quiz_endpoint(payload: RespuestasQuizEntrada):
    """Recibe las 3 respuestas del usuario y devuelve el puntaje obtenido."""
    sesion = obtener_o_crear_sesion(payload.session_id)
    resultado = evaluar_quiz(sesion, payload.respuestas)
    if "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])
    return resultado


@router.get("/temas")
def listar_temas():
    """Lista los temas aprobados por Futuro Academy disponibles en el Tutor."""
    from agente_ia_hu2.base_conocimiento import BASE_CONOCIMIENTO

    return [
        {"id": tema_id, "nombre_visible": tema["nombre_visible"], "fuente": tema["fuente"]}
        for tema_id, tema in BASE_CONOCIMIENTO.items()
    ]
