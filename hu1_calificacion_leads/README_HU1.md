# HU1 · Agente Comercial IA — Calificación Conversacional de Leads

Módulo correspondiente a la **Historia de Usuario 1** del Track 1 (Hackathon de Agentes Financieros IA — AgenticScale). Implementa un agente conversacional que capta, califica y persiste leads en el CRM compartido del equipo, distinguiendo entre prospectos empresariales (B2B) y personas individuales (B2C).

---

## 1. Criterios de aceptación cumplidos

| Criterio (guía oficial) | Cómo se resuelve |
|---|---|
| Identifica si el prospecto es B2B o B2C y aplica preguntas configurables | Clasificación temprana por botones + flujo de preguntas ramificado, definido como estructura de datos configurable (`PREGUNTAS`) |
| Calcula una prioridad simple usando interés, presupuesto, perfil y urgencia | Motor de scoring determinista (`calcular_prioridad`), calibrado contra los 6 leads semilla del CRM |
| Crea o actualiza el contacto, oportunidad y resumen de conversación en un CRM real o simulado | Persistencia vía `shared/database.py` sobre `crm_database.json`, con resumen generado por IA (Gemini + fallback determinista) |

---

## 2. Estructura de archivos

```
hu1_calificacion_leads/
├── __init__.py              # paquete Python
├── agent_commercial.py      # lógica completa: preguntas, scoring, resumen, persistencia, blindaje
├── routes_leads.py          # router FastAPI (montado en main.py de la raíz)
├── streamlit_app.py         # UI de chat conversacional
└── requirements_hu1.txt     # fastapi, uvicorn, pydantic, google-genai, streamlit

test_hu1.py                  # suite de pruebas (raíz del proyecto)
```

`main.py` (raíz) monta el router de HU1:
```python
from hu1_calificacion_leads.routes_leads import router as leads_router
app.include_router(leads_router)
```

---

## 3. Arquitectura del agente

### 3.1 Flujo conversacional

```
apertura (nombre, país)
  → clasificación (B2B / B2C)
  → rama específica (4-6 preguntas según el tipo)
  → cierre (email)
  → cálculo de prioridad + resumen + persistencia en CRM
```

Cada pregunta se define como una estructura configurable que declara a qué campo del schema alimenta, cómo se interpreta la respuesta (texto, número u opción) y si su valor se fusiona con otros dentro de un mismo campo (por ejemplo, cargo y tamaño de empresa se combinan dentro de `perfil`).

### 3.2 Motor de scoring (determinista, no LLM)

La prioridad se calcula con reglas explícitas, sin intervención de IA, por diseño: un número que decide la prioridad de un lead debe ser reproducible y auditable, no depender de que un modelo "interprete bien". La fórmula fue calibrada y verificada contra los 6 leads semilla del CRM original — los 6 casos reproducen exactamente su prioridad real.

| Componente | Puntos |
|---|---|
| Presupuesto (según rango) | 0 a 4 |
| Urgencia (Alta/Media/Baja) | 0 a 2 |
| Tipo de cliente B2B | +1 |
| Tamaño de empresa (B2B) | 0 a 2 |
| Interés en producto formal/regulado | +1 |

`tolerancia_riesgo` se persiste en el CRM pero **no** pesa en el score: es una señal de *fit* (con qué producto encaja el cliente) para la derivación de HU3, no de *valor/intent* del lead — distinción alineada con cómo los CRM financieros separan ambas dimensiones.

### 3.3 Resumen conversacional (Gemini + fallback anti-caída)

Se arma primero una plantilla determinista con los datos disponibles (sin red, sin IA, nunca falla). Luego se intenta mejorar la redacción con Gemini, pasándole esa plantilla como fuente de verdad. Si Gemini falla por cualquier motivo — sin API key, sin librería, sin internet, error del modelo — se captura la excepción y se devuelve la plantilla. El resumen nunca queda vacío ni la demo se cae por un problema de red o cuota de API.

### 3.4 Persistencia en el CRM compartido

El lead se construye y persiste en el orden: cálculo de prioridad → generación de resumen → limpieza de claves internas → generación de ID correlativo (`lead_00N`) → construcción del objeto de dominio → escritura en `crm_database.json` vía las funciones compartidas del equipo.

---

## 4. Enriquecimiento agregado por HU1

Además del núcleo obligatorio, se agregaron dos campos opcionales al schema compartido (no rompen compatibilidad con datos existentes ni con los demás módulos):

- **`empresa_tamano`**: rango de colaboradores para leads B2B. Sí pesa en el score — es señal de valor/fit comercial directo.
- **`tolerancia_riesgo`**: perfil de riesgo para leads B2C. No pesa en el score — informa la derivación y compliance, responsabilidad de HU3.

---

## 5. Interfaz conversacional (Streamlit)

Chat guiado con identidad visual propia (paleta índigo/violeta), que incluye:

- Burbujas de conversación diferenciadas por rol, con efecto de escritura progresiva y un indicador de "escribiendo…" antes de cada respuesta del agente.
- Preguntas de opción cerrada resueltas con botones; preguntas abiertas resueltas con entrada de texto libre.
- Panel lateral con progreso de la conversación en tiempo real, reflejando la máquina de estados del flujo (apertura → clasificación → detalles → contacto).
- Cierre conversacional que **no expone** al prospecto su propio score, prioridad o datos internos de calificación — esa información es responsabilidad y consumo exclusivo del dashboard del ejecutivo comercial (HU3), conforme a como la guía separa ambos roles.

---

## 6. Blindaje y manejo de errores

El módulo fue sometido a una ronda de pruebas de estrés dirigidas a romper el flujo conversacional y la integridad de los datos persistidos. Los hallazgos con impacto real fueron corregidos:

| Área | Problema identificado | Solución aplicada |
|---|---|---|
| Presupuesto | Valores negativos se convertían silenciosamente en positivos | Detección y rechazo explícito de valores ≤ 0, con mensaje específico |
| Presupuesto | Montos absurdamente altos generaban resúmenes ilegibles | Tope máximo configurable, con mensaje específico de confirmación |
| Email | Cualquier texto se aceptaba como correo válido | Validación por expresión regular, con mensaje específico de reintento |
| Texto libre | Respuestas sin límite permitían párrafos excesivos | Truncado silencioso por campo (80 caracteres para nombre, 200 para interés/perfil) |
| Inyección de marcado | Contenido tipo `<script>` podía romper el render de la interfaz o persistirse crudo en el CRM | Doble capa: whitelist de caracteres permitidos en el origen (antes de guardar) + escape de salida en la interfaz (al mostrar) |
| Inyección de prompt | Texto diseñado para secuestrar las instrucciones del modelo de IA | Bloque de reglas de inmunidad en el prompt de generación de resumen: los datos del lead se tratan siempre como contenido a resumir, nunca como instrucciones |
| Datos de contacto (B2B) | El nombre de la persona de contacto se perdía cuando la razón social sobrescribía el campo nombre | Se preserva dentro del perfil del lead como dato de contacto explícito |
| Nombre | Saludos ("Hola") capturados como si fueran el nombre del prospecto | Detección de saludos comunes, con reintento de la pregunta |

**Nota de diseño sobre validación de entradas:** se evaluó y descartó un enfoque de lista negra de palabras y patrones (orientado a amenazas de inyección SQL), por dos razones: la persistencia del proyecto es un archivo JSON plano, no una base de datos SQL, por lo que esa amenaza específica no aplica; y el enfoque de lista negra generaba falsos positivos sobre vocabulario legítimo en español (términos como "inversor" o "sector" contienen la secuencia "OR", usada como palabra clave de bloqueo). Se optó en su lugar por una lista blanca de caracteres permitidos, que neutraliza cualquier símbolo de marcado o control sin restringir el vocabulario del usuario.

---

## 7. Pruebas automatizadas

`test_hu1.py` — suite de 9 casos, ejecutable con o sin `pytest`:

- Calibración del motor de scoring contra los 6 leads semilla del CRM.
- Verificación de que el interés y el tamaño de empresa mueven efectivamente la prioridad calculada.
- Verificación de que la tolerancia al riesgo no afecta el score.
- Generación de resumen: nunca vacío, incluye los datos clave, incorpora contexto sin columna propia (como el país).
- Persistencia: generación correcta de ID correlativo y construcción del registro de dominio sin filtrar claves internas.

Ejecución:
```bash
python test_hu1.py
```

---

## 8. Cómo ejecutar

Desde la raíz del proyecto:

```bash
# Servidor FastAPI (expone el router de HU1)
python -m uvicorn main:app --reload

# Interfaz conversacional
python -m streamlit run hu1_calificacion_leads/streamlit_app.py
```

Variable de entorno opcional para redacción asistida por IA del resumen:
```bash
GEMINI_API_KEY=tu_clave_aquí
```
Sin esta variable, el módulo funciona igual: el resumen se genera con la plantilla determinista.

---

## 9. Decisiones de diseño relevantes

- **Determinismo sobre IA en el scoring:** la prioridad del lead nunca depende de un modelo de lenguaje. Esto respalda una narrativa de auditabilidad y ausencia de alucinación en la decisión comercial más sensible del flujo.
- **Separación de audiencias:** lo que ve el prospecto (interfaz de HU1) y lo que ve el ejecutivo comercial (dashboard de HU3) son experiencias distintas, en línea con cómo la guía oficial redacta cada historia de usuario desde una perspectiva de rol diferente.
- **Compatibilidad como restricción de diseño:** todo campo agregado al schema compartido es opcional y se ubica al final del modelo, garantizando que los datos existentes y el trabajo de los demás módulos del equipo permanezcan intactos ante cualquier cambio.