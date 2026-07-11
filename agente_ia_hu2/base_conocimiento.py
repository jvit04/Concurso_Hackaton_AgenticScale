"""
base_conocimiento.py
---------------------
Contenido educativo "aprobado por Futuro Academy" para el Tutor IA (HU2).

Por qué existe este archivo (y no dejamos que Gemini invente todo):
El criterio de aceptación exige que el Tutor "responda con contenido aprobado por
Futuro Academy e indique la fuente usada". Por eso el conocimiento vive en este
diccionario curado (nuestra "base aprobada"), y el modelo de Gemini solo se usa
para REDACTAR de forma conversacional y amigable ese contenido — nunca para
inventar datos financieros nuevos. Esto también hace la demo más confiable
(no depende 100% de que el LLM responda bien) y cumple el requisito de citar
la fuente en cada respuesta.

Cada tema incluye:
- nombre_visible: cómo se muestra al usuario
- fuente: la referencia que el Tutor debe citar
- resumen: contenido base aprobado (insumo para el LLM, y respaldo si falla la API)
- ruta_aprendizaje: 3 pasos breves sugeridos
- quiz: 3 preguntas de opción múltiple con su respuesta correcta
"""

from typing import Dict, List, Optional

BASE_CONOCIMIENTO: Dict[str, dict] = {
    "ahorro_e_inversion": {
        "nombre_visible": "Ahorro vs. Inversión",
        "fuente": "Futuro Academy - Módulo 1: Fundamentos de Finanzas Personales",
        "resumen": (
            "Ahorrar es guardar dinero sin exponerlo a riesgo, priorizando la "
            "disponibilidad inmediata (ej. un fondo de emergencia). Invertir es "
            "destinar dinero a instrumentos que buscan generar una rentabilidad "
            "futura, asumiendo cierto nivel de riesgo. La recomendación general "
            "es primero construir un colchón de ahorro (3 a 6 meses de gastos) "
            "antes de empezar a invertir."
        ),
        "ruta_aprendizaje": [
            "Calcula tus gastos mensuales fijos y define tu meta de fondo de emergencia.",
            "Aprende la diferencia entre instrumentos de ahorro y de inversión disponibles en tu país.",
            "Define un porcentaje fijo de tus ingresos para ahorrar antes de considerar invertir.",
        ],
        "quiz": [
            {
                "pregunta": "¿Cuál es el objetivo principal de un fondo de emergencia?",
                "opciones": [
                    "Generar la mayor rentabilidad posible",
                    "Tener dinero disponible ante imprevistos",
                    "Pagar impuestos atrasados",
                    "Especular en bolsa a corto plazo",
                ],
                "respuesta_correcta": 1,
            },
            {
                "pregunta": "¿Qué diferencia principal existe entre ahorrar e invertir?",
                "opciones": [
                    "No hay ninguna diferencia real",
                    "Ahorrar siempre rinde más que invertir",
                    "Invertir asume riesgo buscando rentabilidad futura; ahorrar prioriza disponibilidad",
                    "Invertir es solo para empresas, no personas",
                ],
                "respuesta_correcta": 2,
            },
            {
                "pregunta": "Antes de invertir, ¿qué se recomienda tener primero?",
                "opciones": [
                    "Una tarjeta de crédito con límite alto",
                    "Un fondo de emergencia de 3 a 6 meses de gastos",
                    "Un préstamo bancario activo",
                    "No es necesario nada previo",
                ],
                "respuesta_correcta": 1,
            },
        ],
    },
    "interes_compuesto": {
        "nombre_visible": "Interés Compuesto",
        "fuente": "Futuro Academy - Módulo 2: El Poder del Tiempo en tus Finanzas",
        "resumen": (
            "El interés compuesto ocurre cuando los intereses generados por una "
            "inversión se reinvierten, generando a su vez nuevos intereses sobre "
            "el monto total (capital más intereses previos). Esto hace que el "
            "crecimiento no sea lineal sino exponencial con el paso del tiempo, "
            "por lo que empezar a invertir temprano suele tener más impacto que "
            "el monto inicial aportado."
        ),
        "ruta_aprendizaje": [
            "Entiende la fórmula básica: Capital x (1 + tasa)^tiempo.",
            "Compara con una simulación cómo cambia el resultado si empiezas 5 años antes.",
            "Identifica en qué productos de tu banco o academia aplica capitalización compuesta.",
        ],
        "quiz": [
            {
                "pregunta": "¿Qué hace único al interés compuesto frente al interés simple?",
                "opciones": [
                    "Se calcula solo una vez al año",
                    "Los intereses generados también generan nuevos intereses",
                    "Solo aplica a préstamos, no a inversiones",
                    "Siempre es una tasa fija del 5%",
                ],
                "respuesta_correcta": 1,
            },
            {
                "pregunta": "¿Qué variable suele tener más impacto en el interés compuesto a largo plazo?",
                "opciones": [
                    "El color del banco",
                    "El tiempo que el dinero permanece invertido",
                    "El día de la semana en que se invierte",
                    "El número de sucursales del banco",
                ],
                "respuesta_correcta": 1,
            },
            {
                "pregunta": "Si empiezas a invertir 5 años antes con el mismo monto mensual, el resultado final tiende a ser:",
                "opciones": [
                    "Idéntico, el tiempo no afecta",
                    "Menor, porque acumulas más comisiones",
                    "Considerablemente mayor gracias al efecto compuesto",
                    "Imposible de calcular",
                ],
                "respuesta_correcta": 2,
            },
        ],
    },
    "diversificacion": {
        "nombre_visible": "Diversificación de Portafolio",
        "fuente": "Futuro Academy - Módulo 3: Gestión de Riesgo",
        "resumen": (
            "Diversificar significa distribuir el dinero entre distintos tipos de "
            "activos (acciones, bonos, fondos, sectores o geografías) para reducir "
            "el impacto de que uno solo de ellos tenga un mal desempeño. No "
            "elimina el riesgo por completo, pero evita depender del resultado de "
            "una sola inversión."
        ),
        "ruta_aprendizaje": [
            "Identifica las categorías de activos disponibles para ti (renta fija, renta variable, fondos).",
            "Aprende qué es la correlación entre activos y por qué importa al diversificar.",
            "Revisa cómo se distribuye actualmente tu dinero o ahorro entre categorías.",
        ],
        "quiz": [
            {
                "pregunta": "¿Cuál es el objetivo principal de diversificar un portafolio?",
                "opciones": [
                    "Garantizar ganancias sin riesgo",
                    "Reducir el impacto de que una sola inversión falle",
                    "Pagar menos impuestos automáticamente",
                    "Invertir todo en una sola acción prometedora",
                ],
                "respuesta_correcta": 1,
            },
            {
                "pregunta": "¿La diversificación elimina por completo el riesgo de una inversión?",
                "opciones": [
                    "Sí, siempre",
                    "No, pero ayuda a reducir el impacto de pérdidas puntuales",
                    "Solo si inviertes en un único banco",
                    "El riesgo no existe si diversificas",
                ],
                "respuesta_correcta": 1,
            },
            {
                "pregunta": "¿Cuál de estas opciones representa mejor una cartera diversificada?",
                "opciones": [
                    "100% del dinero en una sola acción",
                    "Una combinación de renta fija, renta variable y fondos",
                    "Todo el dinero en efectivo bajo el colchón",
                    "Todo en criptomonedas de un solo proyecto",
                ],
                "respuesta_correcta": 1,
            },
        ],
    },
    "renta_fija_vs_variable": {
        "nombre_visible": "Renta Fija vs. Renta Variable",
        "fuente": "Futuro Academy - Módulo 4: Instrumentos de Inversión",
        "resumen": (
            "La renta fija (como bonos o certificados) ofrece una rentabilidad "
            "predecible y pactada de antemano, con menor riesgo relativo. La "
            "renta variable (como acciones) no garantiza un retorno fijo: puede "
            "generar mayores ganancias, pero también mayores pérdidas, según el "
            "desempeño del mercado."
        ),
        "ruta_aprendizaje": [
            "Compara un ejemplo de instrumento de renta fija con uno de renta variable.",
            "Relaciona tu perfil de riesgo personal con el tipo de instrumento más adecuado.",
            "Investiga qué combinación de ambos ofrecen los productos de Futuro Academy.",
        ],
        "quiz": [
            {
                "pregunta": "¿Qué caracteriza principalmente a la renta fija?",
                "opciones": [
                    "Rentabilidad predecible pactada de antemano",
                    "Rentabilidad siempre superior a la renta variable",
                    "Es exclusiva para empresas grandes",
                    "No tiene ningún riesgo asociado",
                ],
                "respuesta_correcta": 0,
            },
            {
                "pregunta": "En renta variable, el retorno de la inversión:",
                "opciones": [
                    "Está garantizado por ley",
                    "Depende del desempeño del mercado y no está garantizado",
                    "Siempre es fijo y conocido de antemano",
                    "Nunca puede generar pérdidas",
                ],
                "respuesta_correcta": 1,
            },
            {
                "pregunta": "¿Qué debería considerar una persona antes de elegir entre renta fija y variable?",
                "opciones": [
                    "El color de la app del banco",
                    "Su perfil de riesgo y horizonte de tiempo",
                    "Solo el nombre del instrumento",
                    "Nada, ambas son idénticas",
                ],
                "respuesta_correcta": 1,
            },
        ],
    },
}

# Palabras clave para mapear el mensaje libre del usuario a un tema de la base.
PALABRAS_CLAVE: Dict[str, List[str]] = {
    "ahorro_e_inversion": ["ahorro", "ahorrar", "fondo de emergencia", "diferencia entre ahorrar e invertir"],
    "interes_compuesto": ["interes compuesto", "interés compuesto", "capitalizacion", "capitalización"],
    "diversificacion": ["diversificar", "diversificación", "diversificacion", "portafolio", "cartera"],
    "renta_fija_vs_variable": ["renta fija", "renta variable", "bonos", "acciones"],
}


def listar_temas_disponibles() -> List[str]:
    """Devuelve la lista de claves de temas disponibles en la base aprobada."""
    return list(BASE_CONOCIMIENTO.keys())


def obtener_tema(tema_id: str) -> Optional[dict]:
    """Devuelve el contenido aprobado de un tema, o None si no existe."""
    return BASE_CONOCIMIENTO.get(tema_id)


def detectar_tema_por_palabras_clave(mensaje: str) -> Optional[str]:
    """
    Intento simple (sin LLM) de mapear el mensaje del usuario a un tema conocido,
    usado como respaldo rápido o como primer filtro antes de preguntarle a Gemini.
    """
    mensaje_normalizado = mensaje.lower()
    for tema_id, palabras in PALABRAS_CLAVE.items():
        for palabra in palabras:
            if palabra in mensaje_normalizado:
                return tema_id
    return None
