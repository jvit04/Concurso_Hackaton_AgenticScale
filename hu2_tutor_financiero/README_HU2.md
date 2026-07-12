# HU2 · Tutor Financiero IA — Futuro Academy

Módulo correspondiente a la **Historia de Usuario 2** del Track 1 (Hackathon de
Agentes Financieros IA). Implementa el "Tutor IA para Futuro Academy" descrito
en la guía y en `HISTORIA-USUARIO-2.txt`.

## Qué cumple este módulo

| Criterio de aceptación | Cómo se resuelve |
|---|---|
| Responde con contenido aprobado por Futuro Academy e indica la fuente | `base_conocimiento.py` (contenido curado) + Gemini solo redacta ese contenido; toda respuesta incluye `Fuente: ...` |
| Propone ruta breve de aprendizaje o quiz de 3 preguntas | `agent_tutor.py` ofrece ambos caminos; `iniciar_quiz` / `evaluar_quiz` |
| Registra el tema de interés con consentimiento como señal comercial en el CRM | `registrar_interes_en_crm()`, se dispara solo si el usuario responde "sí" |

## Estructura de archivos entregados

```
hu2_tutor_financiero/
├── __init__.py
├── base_conocimiento.py   # Contenido aprobado, fuentes, rutas y quizzes (4 temas)
├── agent_tutor.py          # Lógica del Tutor: Gemini, sesiones, consentimiento, CRM
├── routes_tutor.py         # Router FastAPI para montar en el main.py del equipo
└── cli_tutor.py             # Cliente de consola para pruebas sin FastAPI

requirements_hu2.txt
README_HU2.md
```

Este módulo asume que ya existen en la raíz del proyecto (según lo acordado
con tu equipo):

```
shared/schemas.py    # clase LeadCRM
shared/database.py   # crear_lead, obtener_lead_por_email, actualizar_lead
```

Si esos módulos aún no están disponibles, `agent_tutor.py` no falla al
importarse: simplemente no podrá persistir en el CRM hasta que existan
(`registrar_interes_en_crm` devuelve `False`).

## Instalación

```bash
pip install -r requirements_hu2.txt
export GEMINI_API_KEY="tu_api_key_de_gemini"
```

Si `GEMINI_API_KEY` no está configurada, o falla la llamada a Gemini por
cualquier motivo, el Tutor **igual responde** usando el contenido aprobado
directamente desde `base_conocimiento.py` (sin redacción del LLM), para que
la demo nunca se quede sin respuesta.

## Cómo probarlo rápido (sin FastAPI)

```bash
python -m hu2_tutor_financiero.cli_tutor
```

## Cómo integrarlo al monolito del equipo (FastAPI)

En el `main.py` compartido:

```python
from fastapi import FastAPI
from hu2_tutor_financiero.routes_tutor import router as tutor_router

app = FastAPI()
app.include_router(tutor_router)
```

Endpoints expuestos:

- `POST /tutor/mensaje` → `{ session_id?, email?, mensaje }`
  Flujo conversacional: detecta tema, responde con fuente, pide consentimiento.
- `POST /tutor/quiz/iniciar?session_id=...` → devuelve las 3 preguntas del tema activo.
- `POST /tutor/quiz/responder` → `{ session_id, respuestas: [0,1,2] }` → calcula puntaje.
- `GET /tutor/temas` → lista los temas aprobados disponibles.

## Ejemplo de flujo (curl)

```bash
curl -X POST http://localhost:8000/tutor/mensaje \
  -H "Content-Type: application/json" \
  -d '{"email": "juan@mail.com", "mensaje": "quiero aprender sobre interes compuesto"}'

# El usuario responde "si" para dar consentimiento:
curl -X POST http://localhost:8000/tutor/mensaje \
  -H "Content-Type: application/json" \
  -d '{"session_id": "<el_session_id_devuelto>", "mensaje": "si"}'

curl -X POST "http://localhost:8000/tutor/quiz/iniciar?session_id=<session_id>"

curl -X POST http://localhost:8000/tutor/quiz/responder \
  -H "Content-Type: application/json" \
  -d '{"session_id": "<session_id>", "respuestas": [1, 1, 2]}'
```

## Temas incluidos en la base aprobada (ampliables)

- Ahorro vs. Inversión
- Interés Compuesto
- Diversificación de Portafolio
- Renta Fija vs. Renta Variable

Para añadir un tema nuevo, solo se agrega una entrada al diccionario
`BASE_CONOCIMIENTO` en `base_conocimiento.py` con: `nombre_visible`, `fuente`,
`resumen`, `ruta_aprendizaje` (3 pasos) y `quiz` (3 preguntas de opción
múltiple), y sus palabras clave en `PALABRAS_CLAVE`.

## Notas de diseño

- **Sesiones en memoria**: suficientes para las 48 horas del hackathon. Si el
  servidor se reinicia, se pierden las sesiones activas (no los Leads, que
  viven en el CRM/JSON compartido).
- **Un Lead puede originarse en el Tutor**: si un usuario llega directo al
  Tutor sin pasar por HU1, `registrar_interes_en_crm` crea un Lead mínimo en
  lugar de descartar la señal comercial.
- **Sin asesoría financiera personalizada**: el prompt de Gemini restringe
  explícitamente al modelo a no dar recomendaciones de inversión individuales,
  manteniendo el rol educativo que pide la historia de usuario.
