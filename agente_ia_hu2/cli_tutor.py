"""
cli_tutor.py
-------------
Cliente de consola para probar el Tutor IA (HU2) sin depender de FastAPI ni
del dashboard de HU3. Útil para el Desarrollador B mientras construye la
lógica, o para hacer una demo rápida por terminal.

Uso:
    export GEMINI_API_KEY="tu_api_key"
    python -m agente_ia_hu2.cli_tutor
"""

import sys
from pathlib import Path

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


def _pedir_respuestas_quiz(preguntas) -> list:
    respuestas = []
    for i, pregunta in enumerate(preguntas, start=1):
        print(f"\nPregunta {i}: {pregunta['pregunta']}")
        for idx, opcion in enumerate(pregunta["opciones"]):
            print(f"  {idx}) {opcion}")
        while True:
            try:
                seleccion = int(input("Tu respuesta (número): ").strip())
                if 0 <= seleccion < len(pregunta["opciones"]):
                    respuestas.append(seleccion)
                    break
                print("Número fuera de rango, intenta de nuevo.")
            except ValueError:
                print("Ingresa solo el número de la opción.")
    return respuestas


def main():
    print("=== Tutor IA - Futuro Academy (modo consola) ===")
    email = input("Tu correo (opcional, Enter para omitir): ").strip() or None
    sesion = obtener_o_crear_sesion(email=email)
    print(f"Sesión iniciada: {sesion.session_id}\n")
    print("Escribe 'salir' para terminar en cualquier momento.\n")

    while True:
        mensaje = input("Tú: ").strip()
        if mensaje.lower() in {"salir", "exit", "quit"}:
            print("¡Hasta luego!")
            break

        if mensaje.lower() == "quiz" and sesion.tema_actual:
            quiz = iniciar_quiz(sesion)
            if "error" in quiz:
                print(f"Tutor: {quiz['error']}")
                continue
            print(f"\nTutor: Aquí tienes el quiz de '{quiz['nombre_visible']}' (Fuente: {quiz['fuente']})")
            respuestas = _pedir_respuestas_quiz(quiz["preguntas"])
            resultado = evaluar_quiz(sesion, respuestas)
            print(f"\nTutor: {resultado['mensaje']}")
            continue

        resultado = procesar_mensaje(sesion, mensaje)
        print(f"\nTutor: {resultado['respuesta']}\n")


if __name__ == "__main__":
    main()
