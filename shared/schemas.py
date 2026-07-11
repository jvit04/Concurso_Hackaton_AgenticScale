# shared/schemas.py
from pydantic import BaseModel
from typing import Optional, List

class LeadCRM(BaseModel):
    # --- Datos de Identificación Básica ---
    id: str                         # Un identificador único (ej: "lead_001")
    nombre: str
    email: str
    
    # --- HU1: Datos que recopila el Agente Comercial ---
    tipo_cliente: str               # "B2B" (Empresa) o "B2C" (Persona individual)
    interes: str                    # Qué necesidad financiera tiene
    presupuesto: float              # Cuánto dinero dispone
    perfil: str                     # Características del cliente
    urgencia: str                   # "Alta", "Media", "Baja"
    prioridad: str                  # Calculada automáticamente: "Alta", "Media", "Baja"
    resumen_conversacion_comercial: str # Contexto de la charla con el primer agente

    # --- HU2: Datos que recopila el Tutor IA ---
    tema_aprendizaje: Optional[str] = None  # Qué tema financiero investigó en la academia
    score_quiz: Optional[int] = None        # Cuántas preguntas del quiz de 3 preguntas respondió bien
    consentimiento_registro: bool = False   # ¿Dio permiso para guardar sus datos comerciales? (True/False)

    # --- HU3: Datos para el Dashboard del Ejecutivo ---
    accion_propuesta: Optional[str] = None # "Agendar reunión", "Enviar material", etc.[cite: 1]
    estado_accion: str = "Pendiente"       # "Pendiente", "Aprobado", "Editado", "Rechazado"[cite: 1]