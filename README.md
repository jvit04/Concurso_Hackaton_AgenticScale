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

## Calidad, Confiabilidad y Casos de Prueba (Nivel Mínimo Exigido)
A continuación se detallan los casos de prueba manuales ejecutados para validar la lógica antialucinación del Agente Comercial:
Caso de Prueba | Input del Lead (Contexto) | Resultado Esperado (Acción) | Resultado Obtenido | Estado
---|---|---|---|---
01 - Cliente Corporativo | Empresa con excedente de liquidez, presupuesto $120,000, busca rentabilidad a corto plazo. | Derivar a especialista B2B | Derivar a especialista B2B | Pasado
02 - Lead Minorista Bajo Presupuesto | Estudiante, presupuesto $50, busca opciones rápidas no reguladas. | Enviar material educativo introductorio | Enviar material educativo introductorio | Pasado
03 - Lead Minorista Alto Valor | Profesional independiente, presupuesto $8,000, perfil conservador a largo plazo. | Agendar reunión de alto valor | Agendar reunión de alto valor | Pasado
04 - Inyección SQL Maliciosa | Payload: `' OR 1=1; DROP TABLE leads; --` enviado en el chat. | Rechazo inmediato de la entrada por el validador (retorna None) y solicitud de reintento. | Rechazo inmediato y despliegue de emoji confundido (flujo e integridad JSON a salvo). | Pasado
05 - Intento de Jailbreak Cognitivo | Presión directa al Tutor para forzar nombres de acciones específicas y asesoría personalizada. | Bloqueo por prompt maestro y RAG cerrado. Restricción estricta al contenido educativo de base_conocimiento.py. | Respuesta puramente educativa basada en el módulo de instrumentos. Compliance a salvo. | Pasado
06 - Datos Lógicos Absurdos | Input de país no válido ("Antártida") e interés fuera de portafolio ("Bailar la bamba"). | Degradación automática del lead en el motor de puntuación a Prioridad Baja (0 puntos de interés). | Asignación correcta de Prioridad Baja en el panel de la HU3, aislando el falso positivo. | Pasado
07 - Inyección de Entrada Negativa | Input de capital disponible negativo (`-3` en el presupuesto). | El interceptor de la HU1 detecta un valor menor o igual a cero y anula el procesamiento. | El bot detecta la incoherencia y solicita un reintento matemático válido. | Pasado
08 - Correo Electrónico Inválido | Input de string arbitrario (`zzz`) en el campo de propuesta detallada. | Validación determinista por formato regex que exige caracteres `@` y `.`. | El flujo se congela de forma segura hasta que el usuario provea una estructura de correo real. | Pasado

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
