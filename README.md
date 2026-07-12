# AgenticScale - CRM Financiero Inteligente (Track 1)
Evento: Agentic Scale Ecuador Tech Week 2026 | Periodo: 2026-1 | Estado: Completado

## Equipo de trabajo
- Diego Moscol ([Fergaku](https://github.com/Fergaku/Fergaku))
- Eddy Lima ([elima-hub](https://github.com/elima-hub))
- José Viteri ([jvit04](https://github.com/jvit04))

## Capturas / Demo
![hu1_1](docs/screenshots/hu1_1.png)
![hu1_2](docs/screenshots/hu1_2.png)
![hu2_1](docs/screenshots/hu2_1.png)
![hu2_2](docs/screenshots/hu2_2.png)
![hu3_1](docs/screenshots/hu3_1.png)
![hu3_2](docs/screenshots/hu3_2.png)
![hu3_3](docs/screenshots/hu3_3.png)
![hu3_4](docs/screenshots/hu3_4.png)




*(Link de despliegue en producción: [Insertar enlace de Streamlit Community Cloud aquí])*

## Funcionalidad Multi-Agente
- [x] **HU1 - Agente Comercial de Captación y Calificación:** Interfaz interactiva de chat orientada a la recopilación de datos, segmentación inicial y perfilamiento estructurado de los leads entrantes.
- [x] **HU2 - Tutor Financiero Automatizado (Futuro Academy):** Motor educativo guiado por IA que convierte el aprendizaje en intención comercial, evalúa el rendimiento en quizzes financieros y gestiona el consentimiento regulatorio de datos.
- [x] **HU3 - Panel de Control Comercial Asistido por IA:** Dashboard directivo minimalista que procesa leads entrantes, renderiza métricas operativas con Pandas y utiliza la API de Google Gemini para proponer acciones comerciales estructuradas (Agendar, Enviar material | Derivar B2B) manteniendo la validación humana en el bucle ("Human-in-the-Loop").

## Tecnologías
`Python` `Streamlit` `Google GenAI SDK` `Pandas` `JSON` `Git`

## Ejecución
### Instrucciones paso a paso para Evaluación

#### Opción 1: Acceso Directo al Despliegue en la Nube (Recomendado)
1. Ingrese de manera directa al enlace de producción alojado en Streamlit Cloud: `[Insertar URL de Streamlit Cloud]`.
2. Explore el Resumen Operativo y apruebe/rechace acciones en tiempo real sobre los datos históricos cargados.

#### Opción 2: Despliegue Técnico Local (Vía Terminal)
1. Clone el repositorio remoto y acceda al directorio raíz:
```bash
git clone [https://github.com/jvit04/Concurso_Hackaton_AgenticScale.git](https://github.com/jvit04/Concurso_Hackaton_AgenticScale.git)
cd Concurso_Hackaton_AgenticScale
```
2. Instale las dependencias oficiales requeridas:
```bash
pip install streamlit google-genai pandas python-dotenv
```
3. Configure sus credenciales locales. Cree el archivo .streamlit/secrets.toml y añada su API Key:
```bash
GEMINI_API_KEY = "Tu_Clave_Privada_De_Google"
```
4. Ejecute el panel de control del agente comercial:
```bash
python -m streamlit run hu3_seguimiento_comercial/app.py
```

#### Opción 3: Ejecución del Agente Comercial de Captación (HU1)
El módulo HU1 se expone tanto como interfaz conversacional (Streamlit) como router de API (FastAPI), y ambos consumen la misma lógica de negocio.

1. Instale las dependencias propias del módulo (si no se instalaron ya en el paso anterior):
```bash
pip install -r hu1_calificacion_leads/requirements_hu1.txt
```
2. Levante el servidor FastAPI (expone el router de captación de leads sobre `main.py`):
```bash
python -m uvicorn main:app --reload
```
3. En una terminal separada, levante la interfaz conversacional del Agente Comercial:
```bash
python -m streamlit run hu1_calificacion_leads/streamlit_app.py
```
4. (Opcional) Ejecute la suite de pruebas automatizadas del módulo:
```bash
python test_hu1.py
```

## Calidad, Confiabilidad y Casos de Prueba (Nivel Mínimo Exigido)
A continuación se detallan los casos de prueba manuales ejecutados para validar la lógica antialucinación del Agente Comercial:
Caso de Prueba | Componente / Input | Comportamiento Esperado | Resultado Obtenido | Estado
---|---|---|---|---
**01 - Corp.** | HU1 - Segmento B2B | Presupuesto $120k con urgencia media. | Derivar a especialista B2B. | Pasado
**02 - Retail Min.**| HU1 - Segmento B2C | Presupuesto $50 con interés informal. | Enviar material educativo introductorio. | Pasado
**03 - Retail Alto**| HU1 - Segmento B2C | Presupuesto $8k con perfil conservador. | Agendar reunión de alto valor. | Pasado
**A1 - Letras** | HU1 - Presupuesto | Usuario escribe el monto con letras ("diez mil"). | Interceptor activa re-pregunta genérica. | Pasado
**A2 - Negativo** | HU1 - Presupuesto | Usuario ingresa un capital negativo (`-3`). | Mensaje específico de error; no se muta a positivo. | Pasado
**A3 - Absurdo** | HU1 - Presupuesto | Entrada de valores numéricos incoherentes. | Mensaje de restricción de negocio; no se acepta. | Pasado
**B1 - Email** | HU1 - Contacto | Entrada de cadenas sin formato válido (`zzz`). | Mensaje de advertencia específico; el flujo no avanza. | Pasado
**C1 - XSS Chat** | HU1 - Burbujas | Intento de inyectar etiquetas `<script>` o HTML. | El motor escapa los caracteres; se lee literal, no ejecuta. | Pasado
**C2 - XSS Base** | HU1 - Base de Datos| Inyección de código destinada a persistencia. | Símbolos peligrosos removidos del JSON; texto limpio. | Pasado
**C3 - Flexibilidad**| HU1 - Perfilamiento| Input libre `"inversor/sector"`. | Pasa de forma nativa sin rechazo de concordancia. | Pasado
**C4 - SQL Plano** | HU1 - Entrada libre | Comando `DROP TABLE leads; --` como nombre. | Neutralizado en base de datos; se almacena como texto plano. | Pasado
**D1 - Desborde** | HU1 - Campo de texto| Entrada de texto masivo y redundante. | Sanitización activa: truncado a 200/80 caracteres en el JSON. | Pasado
**E1 - Hijacking** | HU2 - Gemini Prompt | Orden de olvidar instrucciones e inventar marcas. | El prompt fusionado e inmune anula el payload. Gemini no obedece. | Pasado
**F1 - Multi-Opc.** | HU1 - Segmentación| Intento de doble envío en botones de opción. | No aplica; el control por botones nativos bloquea colisiones. | Pasado
**F2 - Vacío** | HU1 - Entrada libre | Envío de múltiples espacios o inputs vacíos. | El sistema intercepta el nulo; no ensucia la interfaz del chat. | Pasado
**F3 - Idempot.** | Streamlit Lifecycle | Recarga manual de la pestaña del navegador. | Reinicia el estado de sesión de forma limpia (Comportamiento esperado).| Pasado
**F4 - Race Cond.**| Streamlit UI | Usuario ejecuta un doble clic rápido en un botón. | Se procesa bajo un semáforo lógico; actúa como un solo clic. | Pasado
**G1 - Unit Tests**| Backend general | Ejecución de suite automatizada `test_hu1.py`. | 9/9 unit tests aprobados con calibración intacta. | Pasado

## Detalle del Módulo HU1 — Agente Comercial IA

### Estructura de archivos
```
hu1_calificacion_leads/
├── __init__.py
├── agent_commercial.py      # preguntas configurables, scoring, resumen IA, persistencia, blindaje
├── routes_leads.py          # router FastAPI montado en main.py
├── streamlit_app.py         # interfaz conversacional
└── requirements_hu1.txt

test_hu1.py                  # suite de pruebas (raíz del proyecto)
```

### Motor de scoring (determinista)
La prioridad del lead se calcula con reglas explícitas, sin intervención de un modelo de lenguaje, para mantener el resultado reproducible y auditable. La fórmula fue calibrada contra los 6 leads semilla originales del CRM, a los que reproduce exactamente.

| Componente | Aporte al score |
|---|---|
| Presupuesto | 0 a 4 puntos según rango |
| Urgencia | 0 a 2 puntos |
| Tipo de cliente B2B | +1 punto |
| Tamaño de empresa (B2B) | 0 a 2 puntos |
| Interés en producto formal/regulado | +1 punto |

La tolerancia al riesgo (leads B2C) se persiste en el CRM pero no pesa en el score: es una señal de encaje de producto (*fit*) para la derivación comercial de HU3, no de valor del lead.

### Enriquecimiento del schema compartido
Se agregaron dos campos opcionales a `LeadCRM`, sin romper compatibilidad con los datos existentes ni con los demás módulos:
- `empresa_tamano` — rango de colaboradores para leads B2B (pesa en el score).
- `tolerancia_riesgo` — perfil de riesgo para leads B2C (informa la derivación de HU3).

### Resumen conversacional con recuperación ante fallos
El resumen de cada lead se arma primero con una plantilla determinista y luego se intenta enriquecer con Gemini. Si la API no está disponible por cualquier motivo, el sistema utiliza la plantilla sin interrumpir el flujo, garantizando que la demostración nunca se detenga por una dependencia externa.

### Separación de audiencias en la interfaz
La interfaz conversacional de HU1 no expone al prospecto su propio score ni los datos internos de calificación: esa información es consumo exclusivo del panel del ejecutivo comercial (HU3), en línea con cómo la guía del hackathon redacta cada historia de usuario desde un rol distinto.

## Métricas de Progreso
| Indicador | Valor |
|---|---|
| Total de Leads en Base Inicial | 6 Registros Estructurados |
| Estado de Implementación | 100% Funcional (Fase 1) |
| Cobertura de Pruebas Manuales | Casos Críticos de Mitigación de Riesgos Validados |
| Última actualización | 2026-07-12 |

## Reflexión y Aprendizajes (Conceptos Clave del Evento)
- **Habilidades desarrolladas:** Integración del nuevo SDK de google-genai para orquestación de prompts financieros cerrados, optimización de flujos de trabajo directivos mediante componentes visuales de Streamlit y control preventivo de conflictos en Git mediante aislamiento de datos asíncronos.
- **Mitigación de Riesgos:** Aplicación de ingeniería de prompts estricta para forzar respuestas categóricas en el LLM, eliminando por completo el riesgo de alucinación de datos financieros o tasas de interés inventadas.

- **Qué se podría mejorar:** Evolucionar la persistencia de datos local basada en archivos estructurados JSON hacia una base de datos distribuida en la nube (como PostgreSQL o Neon) para entornos empresariales de alta concurrencia.