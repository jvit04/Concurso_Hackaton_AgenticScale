"""
HU1 · Agente Comercial IA — Calificación conversacional de leads
=================================================================
Track 1 (Hackathon de Agentes Financieros IA).

Este módulo cubre la lógica de la Historia de Usuario 1:
  1) Detecta si el prospecto es B2B o B2C y aplica preguntas configurables.
  2) [Fase 2] Calcula una prioridad simple (interés, presupuesto, perfil, urgencia).
  3) [Fase 4] Crea/actualiza el lead en el CRM compartido.

ESTADO POR FASES
  - Fase 1 (implementado): PREGUNTAS, construir_flujo, parseo de respuestas,
    ensamblado del 'perfil' por fusión, armado del dict de datos.
  - Fase 2 (stub): calcular_prioridad()
  - Fase 3 (stub): generar_resumen()  -> Gemini + fallback determinista
  - Fase 4 (stub): guardar_lead()     -> construye LeadCRM y persiste vía shared.database
"""

from typing import Optional


# =====================================================================
# FASE 1 — PREGUNTAS CONFIGURABLES B2B / B2C
# =====================================================================
# Cada pregunta declara:
#   id       : identificador interno
#   texto    : lo que ve el usuario
#   tipo     : "texto" | "numero" | "opcion"
#   destino  : campo del LeadCRM (o "resumen" para datos sin columna propia)
#   fusion   : True -> se ACUMULA en el destino (no lo sobrescribe)
#   opciones : solo tipo "opcion"; mapea lo dicho por el usuario al valor del schema

PREGUNTAS_COMUNES_APERTURA = [
    {
        "id": "nombre",
        "texto": "Hola, soy tu asistente virtual. Para empezar, ¿con quién tengo el gusto de hablar?",
        "tipo": "texto",
        "destino": "nombre",
        "fusion": False,
    },
    {
        "id": "pais",
        "texto": "¿Desde qué país nos contactas?",
        "tipo": "texto",
        "destino": "resumen",   # sin columna propia en el schema; se teje en el resumen
        "fusion": True,
    },
]

PREGUNTA_CLASIFICACION = {
    "id": "tipo_cliente",
    "texto": "¡Un placer! Cuéntame, ¿buscas una solución financiera para tu empresa o para ti a nivel personal?",
    "tipo": "opcion",
    "destino": "tipo_cliente",
    "fusion": False,
    "opciones": {
        "empresa": "B2B",
        "empresarial": "B2B",
        "negocio": "B2B",
        "individual": "B2C",
        "personal": "B2C",
        "para mi": "B2C",
        "para mí": "B2C",
    },
}

PREGUNTAS_B2B = [
    {
        "id": "empresa_nombre",
        "texto": "Perfecto. ¿Cuál es el nombre o razón social de la empresa?",
        "tipo": "texto",
        "destino": "nombre",   # en B2B el 'nombre' del lead es la razón social
        "fusion": False,
    },
    {
        "id": "contacto_cargo",
        "texto": "¿Qué rol o cargo desempeñas dentro de la organización?",
        "tipo": "texto",
        "destino": "perfil",   # fusionado: ¿es el tomador de decisión?
        "fusion": True,
    },
    {
        "id": "interes_b2b",
        "texto": ("¿Cuál es la principal necesidad financiera que buscan resolver hoy? "
                  "(por ejemplo: inversión de excedentes, capital de trabajo, línea de crédito u otra)"),
        "tipo": "texto",
        "destino": "interes",
        "fusion": False,
    },
    {
        "id": "monto_operacion",
        "texto": "¿Qué monto aproximado en USD están considerando para esta operación?",
        "tipo": "numero",
        "destino": "presupuesto",
        "fusion": False,
    },
    {
        "id": "empresa_tamano",
        "texto": ("Para entender mejor su estructura, ¿cuántos colaboradores tienen aproximadamente? "
                  "(1-10, 11-50, 51-200, o más de 200)"),
        "tipo": "opcion",
        "destino": "empresa_tamano",   # campo nuevo del schema; pesa en el score (Fase 2)
        "fusion": False,
        "opciones": {
            "1-10": "1-10",
            "11-50": "11-50",
            "51-200": "51-200",
            "más de 200": "Más de 200",
            "mas de 200": "Más de 200",
        },
    },
    {
        "id": "urgencia_b2b",
        "texto": ("¿Para cuándo tienen planeado ejecutar este proyecto? "
                  "(este mes, en los próximos 3 meses, o solo están explorando)"),
        "tipo": "opcion",
        "destino": "urgencia",
        "fusion": False,
        "opciones": {
            "este mes": "Alta",
            "proximos 3 meses": "Media",
            "próximos 3 meses": "Media",
            "3 meses": "Media",
            "explorando": "Baja",
            "solo explorando": "Baja",
        },
    },
]

PREGUNTAS_B2C = [
    {
        "id": "interes_b2c",
        "texto": ("Excelente. ¿Cuál es tu principal objetivo financiero en este momento? "
                  "(por ejemplo: plan de retiro, multiplicar tus ahorros, tu primera inversión "
                  "o crear un fondo de emergencia)"),
        "tipo": "texto",
        "destino": "interes",
        "fusion": False,
    },
    {
        "id": "monto_inversion",
        "texto": "¿Qué capital aproximado en USD tienes disponible para comenzar?",
        "tipo": "numero",
        "destino": "presupuesto",
        "fusion": False,
    },
    {
        "id": "perfil_riesgo",
        "texto": ("En el mundo de las inversiones, ¿cómo te consideras respecto al riesgo? "
                  "(conservador: prefieres seguridad; moderado; o agresivo: buscas alto rendimiento)"),
        "tipo": "opcion",
        "destino": "tolerancia_riesgo",   # campo nuevo; NO pesa en el score (fit/compliance)
        "fusion": False,
        "opciones": {
            "conservador": "Conservador",
            "conservadora": "Conservador",
            "seguridad": "Conservador",
            "moderado": "Moderado",
            "moderada": "Moderado",
            "agresivo": "Agresivo",
            "agresiva": "Agresivo",
            "alto rendimiento": "Agresivo",
        },
    },
    {
        "id": "urgencia_b2c",
        "texto": ("¿Qué tan pronto te gustaría ver colocado tu capital? "
                  "(de inmediato, en unos meses, o aún lo estás pensando)"),
        "tipo": "opcion",
        "destino": "urgencia",
        "fusion": False,
        "opciones": {
            "de inmediato": "Alta",
            "inmediato": "Alta",
            "ya": "Alta",
            "en unos meses": "Media",
            "unos meses": "Media",
            "pensando": "Baja",
            "aun lo estoy pensando": "Baja",
            "aún lo estoy pensando": "Baja",
        },
    },
]

PREGUNTAS_COMUNES_CIERRE = [
    {
        "id": "email",
        "texto": ("¡Muchas gracias por tus respuestas! Ya casi tengo tu perfil listo. "
                  "¿A qué correo electrónico te enviamos la propuesta detallada?"),
        "tipo": "texto",
        "destino": "email",
        "fusion": False,
    },
]

# Ramas específicas (configurable: agregar/quitar = editar estas listas)
PREGUNTAS = {
    "B2B": PREGUNTAS_B2B,
    "B2C": PREGUNTAS_B2C,
}


def construir_flujo(tipo_cliente: str) -> list:
    """
    Secuencia ORDENADA de preguntas para un lead ya clasificado.
    Orden: apertura -> rama (B2B/B2C) -> cierre.

    La clasificación (PREGUNTA_CLASIFICACION) se hace ANTES, porque es la
    que determina 'tipo_cliente'. El orquestador (Streamlit/CLI, Fase 5) hará:
        apertura -> clasificación -> construir_flujo(tipo) -> cierre
    Aquí incluimos apertura+cierre para que el flujo por rama quede completo
    y testeable de forma aislada.
    """
    rama = PREGUNTAS.get(tipo_cliente, [])
    return PREGUNTAS_COMUNES_APERTURA + rama + PREGUNTAS_COMUNES_CIERRE


# =====================================================================
# FASE 1 — PARSEO DE RESPUESTAS
# =====================================================================
def normalizar(texto: str) -> str:
    """Minúsculas + sin espacios sobrantes, para comparar contra 'opciones'."""
    return (texto or "").strip().lower()


def parsear_opcion(pregunta: dict, respuesta_usuario: str) -> Optional[str]:
    """
    Traduce lo que dijo el usuario al valor exacto del schema, usando el dict
    'opciones'. Busca coincidencia por inclusión (el usuario puede escribir de más).
    Devuelve None si no reconoce la respuesta (el orquestador puede re-preguntar).
    """
    opciones = pregunta.get("opciones", {})
    r = normalizar(respuesta_usuario)
    # 1) match exacto
    if r in opciones:
        return opciones[r]
    # 2) match por inclusión (ej. "somos como 11-50 personas" -> "11-50")
    for clave, valor in opciones.items():
        if clave in r:
            return valor
    return None


def parsear_numero(respuesta_usuario: str) -> Optional[float]:
    """
    Extrae un número de una respuesta libre. Tolera '$', comas, 'usd', 'mil'.
    Ej: '$120,000' -> 120000.0 ; 'unos 8 mil' -> 8000.0
    Devuelve None si no encuentra número (el orquestador re-pregunta).
    """
    r = normalizar(respuesta_usuario)
    tiene_mil = "mil" in r
    # deja solo dígitos, punto y coma
    limpio = "".join(c for c in r if c.isdigit() or c in ".,")
    limpio = limpio.replace(",", "")  # comas = separador de miles
    if not limpio:
        return None
    try:
        valor = float(limpio)
    except ValueError:
        return None
    if tiene_mil and valor < 1000:   # "8 mil" -> 8000
        valor *= 1000
    return valor


def interpretar_respuesta(pregunta: dict, respuesta_usuario: str):
    """
    Devuelve el valor ya tipado/mapeado según el 'tipo' de la pregunta:
      - "opcion" -> valor del schema (str) o None
      - "numero" -> float o None
      - "texto"  -> string tal cual (limpiado)
    """
    tipo = pregunta.get("tipo", "texto")
    if tipo == "opcion":
        return parsear_opcion(pregunta, respuesta_usuario)
    if tipo == "numero":
        return parsear_numero(respuesta_usuario)
    return (respuesta_usuario or "").strip()


# =====================================================================
# FASE 1 — ENSAMBLADO DE DATOS (mapa pregunta -> campo del schema)
# =====================================================================
def ensamblar_datos(respuestas: list) -> dict:
    """
    Recibe una lista de (pregunta, valor_interpretado) en el orden del flujo
    y arma el diccionario de datos listo para el schema.

    Reglas:
      - Campos con fusion=False: se asignan directo (el último gana si se repite).
      - Campos con fusion=True : se ACUMULAN en una lista, luego se unen con ' — '.
      - 'empresa_tamano' se guarda en su campo Y también se refleja legible en perfil.
      - destino "resumen": se acumula aparte, para que Fase 3 lo teja en el texto.

    Devuelve un dict como:
      {
        "nombre": "...", "email": "...", "tipo_cliente": "B2B",
        "interes": "...", "presupuesto": 120000.0, "urgencia": "Media",
        "empresa_tamano": "51-200", "tolerancia_riesgo": None,
        "perfil": "Gerente Financiero — Empresa de 51-200 colaboradores",
        "_contexto_resumen": ["País: Ecuador"]   # material para el resumen (Fase 3)
      }
    """
    datos = {}
    fusion_perfil = []
    contexto_resumen = []

    for pregunta, valor in respuestas:
        if valor in (None, ""):
            continue  # respuesta no reconocida o vacía: no ensuciamos el dict
        destino = pregunta["destino"]
        fusion = pregunta.get("fusion", False)

        if destino == "resumen":
            contexto_resumen.append(f"{_etiqueta(pregunta)}: {valor}")
            continue

        if fusion and destino == "perfil":
            fusion_perfil.append(str(valor))
            continue

        # asignación directa
        datos[destino] = valor

        # reflejar empresa_tamano también en el perfil (legible)
        if destino == "empresa_tamano":
            fusion_perfil.append(f"Empresa de {valor} colaboradores")

    # construir el campo 'perfil' final por fusión
    if fusion_perfil:
        perfil_previo = datos.get("perfil", "")
        partes = ([perfil_previo] if perfil_previo else []) + fusion_perfil
        datos["perfil"] = " — ".join(partes)

    if contexto_resumen:
        datos["_contexto_resumen"] = contexto_resumen

    return datos


def _etiqueta(pregunta: dict) -> str:
    """Etiqueta legible para el contexto del resumen (a partir del id)."""
    etiquetas = {
        "pais": "País",
    }
    return etiquetas.get(pregunta["id"], pregunta["id"].capitalize())


# =====================================================================
# FASE 2 — SCORING (stub, se implementa en la siguiente fase)
# =====================================================================
def calcular_prioridad(tipo_cliente: str, presupuesto: float, urgencia: str,
                       interes: str = "", empresa_tamano: Optional[str] = None) -> str:
    """
    [Fase 2] Devuelve 'Alta' | 'Media' | 'Baja' con una fórmula determinista
    calibrada contra los leads semilla. tolerancia_riesgo NO entra aquí (es fit).
    """
    raise NotImplementedError("Se implementa en Fase 2")


# =====================================================================
# FASE 3 — RESUMEN CON GEMINI + FALLBACK (stub)
# =====================================================================
def generar_resumen(datos: dict) -> str:
    """
    [Fase 3] Redacta 'resumen_conversacion_comercial' a partir de datos ya
    recopilados (Gemini narra; nunca inventa cifras). Si no hay API key o falla,
    arma el resumen con una plantilla determinista usando datos['_contexto_resumen'].
    """
    raise NotImplementedError("Se implementa en Fase 3")


# =====================================================================
# FASE 4 — PERSISTENCIA EN CRM (stub)
# =====================================================================
def guardar_lead(datos: dict):
    """
    [Fase 4] Construye un LeadCRM con los datos ensamblados + prioridad + resumen,
    genera el id correlativo (lead_00N) y lo persiste con shared.database.crear_lead.
    """
    raise NotImplementedError("Se implementa en Fase 4")