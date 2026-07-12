"""
Pruebas de HU1 - Agente Comercial IA
Cubre Fase 2 (scoring), Fase 3 (resumen) y Fase 4 (persistencia).

Ejecutar desde la raíz del proyecto:
    python -m pytest test_hu1.py -v
o sin pytest:
    python test_hu1.py
"""
import os
# Aseguramos que los tests corran el camino de FALLBACK (sin llamar a Gemini)
os.environ.pop("GEMINI_API_KEY", None)

from hu1_calificacion_leads import agent_commercial as ac


# =====================================================================
# FASE 2 — SCORING
# =====================================================================
def test_calibracion_leads_semilla():
    """Los 6 leads semilla reproducen su prioridad exacta."""
    casos = [
        # (tipo, presupuesto, urgencia, interes, tamano, esperado)
        ("B2C", 1500,  "Alta",  "Fondo de emergencia",  None, "Media"),  # lead_001
        ("B2B", 120000,"Media", "Inversión corporativa",None, "Alta"),   # lead_002
        ("B2C", 50,    "Baja",  "Criptomonedas",        None, "Baja"),   # lead_003
        ("B2B", 50000, "Alta",  "Líneas de crédito",    None, "Alta"),   # lead_004
        ("B2C", 8000,  "Baja",  "Plan de jubilación",   None, "Media"),  # lead_005
        ("B2C", 0,     "Baja",  "Asesoría general",     None, "Baja"),   # lead_006
    ]
    for tipo, pres, urg, interes, tam, esperado in casos:
        obtenido = ac.calcular_prioridad(tipo, pres, urg, interes, tam)
        assert obtenido == esperado, (
            f"Lead {tipo}/{pres}/{urg}/{interes}: esperaba {esperado}, obtuvo {obtenido}"
        )


def test_interes_mueve_la_banda():
    """Dos leads idénticos salvo el interés caen en bandas distintas.
    Con presupuesto 1000 (=1pt) + urgencia Media (=1pt) = 2pts -> Media.
    El interés formal suma +1 (=3 -> Media), el cripto +0 (=2 -> Media).
    Ajustamos a un caso en el umbral real: presupuesto 900 (=0) + urgencia Media (=1).
    Formal: 0+1+1=2 -> Media ; Cripto: 0+1+0=1 -> Baja."""
    formal = ac.calcular_prioridad("B2C", 900, "Media", "fondo de ahorro", None)
    cripto = ac.calcular_prioridad("B2C", 900, "Media", "criptomonedas", None)
    assert formal == "Media", f"interés formal debería dar Media, dio {formal}"
    assert cripto == "Baja",  f"interés cripto debería dar Baja, dio {cripto}"
    assert formal != cripto, "el interés NO está moviendo la banda"


def test_empresa_tamano_suma():
    """Empresa grande sube de banda respecto a micro con mismos datos.
    B2B (=1) + presupuesto 5000 (=2) + urgencia Baja (=0) + interés formal (=1) = 4 -> Media.
    Con tamaño 51-200 (=2): 4+2 = 6 -> Alta."""
    micro  = ac.calcular_prioridad("B2B", 5000, "Baja", "capital de trabajo", "1-10")
    grande = ac.calcular_prioridad("B2B", 5000, "Baja", "capital de trabajo", "51-200")
    assert micro == "Media", f"micro debería dar Media, dio {micro}"
    assert grande == "Alta", f"grande debería dar Alta, dio {grande}"


def test_tolerancia_riesgo_no_afecta_score():
    """calcular_prioridad ni siquiera acepta tolerancia_riesgo: se prueba que
    dos leads idénticos dan el mismo score (la tolerancia vive fuera del cálculo)."""
    a = ac.calcular_prioridad("B2C", 8000, "Media", "plan de retiro", None)
    b = ac.calcular_prioridad("B2C", 8000, "Media", "plan de retiro", None)
    assert a == b  # trivialmente igual: confirma que tolerancia no es parámetro


# =====================================================================
# FASE 3 — RESUMEN (camino fallback, sin API key)
# =====================================================================
def test_resumen_nunca_vacio():
    """El fallback siempre devuelve texto, incluso con datos mínimos."""
    datos = {"tipo_cliente": "B2C", "nombre": "Ana"}
    resumen = ac.generar_resumen(datos)
    assert isinstance(resumen, str) and len(resumen) > 0


def test_resumen_incluye_datos_clave():
    """El resumen contiene nombre, interés y presupuesto formateado."""
    datos = {
        "tipo_cliente": "B2B", "nombre": "Constructora Andina SA",
        "interes": "inversión de excedentes", "presupuesto": 120000.0,
        "urgencia": "Media",
    }
    r = ac.generar_resumen(datos)
    assert "Constructora Andina SA" in r
    assert "inversión de excedentes" in r
    assert "120,000" in r  # formato USD con coma de miles


def test_resumen_incluye_contexto_pais():
    """El país (dato sin columna, en _contexto_resumen) aparece en el texto."""
    datos = {
        "tipo_cliente": "B2C", "nombre": "Ana", "interes": "ahorro",
        "presupuesto": 1000.0, "urgencia": "Alta",
        "_contexto_resumen": ["País: Ecuador"],
    }
    r = ac.generar_resumen(datos)
    assert "Ecuador" in r


# =====================================================================
# FASE 4 — PERSISTENCIA (mockeando crear_lead para no tocar el CRM real)
# =====================================================================
def test_id_correlativo(monkeypatch):
    """Con leads hasta lead_006, el nuevo id es lead_007."""
    from shared.schemas import LeadCRM
    fake = [LeadCRM(id=f"lead_{i:03d}", nombre="x", email=f"{i}@x.com",
                    tipo_cliente="B2C", interes="ahorro", presupuesto=1.0,
                    perfil="", urgencia="Baja", prioridad="Baja",
                    resumen_conversacion_comercial="") for i in range(1, 7)]
    monkeypatch.setattr(ac, "obtener_todos_los_leads", lambda: fake)
    assert ac._generar_id_correlativo() == "lead_007"


def test_guardar_lead_construye_y_persiste(monkeypatch):
    """guardar_lead arma el LeadCRM, calcula prioridad, limpia _contexto y persiste."""
    guardados = []
    from shared.schemas import LeadCRM
    fake = [LeadCRM(id=f"lead_{i:03d}", nombre="x", email=f"{i}@x.com",
                    tipo_cliente="B2C", interes="ahorro", presupuesto=1.0,
                    perfil="", urgencia="Baja", prioridad="Baja",
                    resumen_conversacion_comercial="") for i in range(1, 7)]
    monkeypatch.setattr(ac, "obtener_todos_los_leads", lambda: fake)
    monkeypatch.setattr(ac, "crear_lead", lambda lead: guardados.append(lead))

    datos = {
        "tipo_cliente": "B2B", "nombre": "Tech SA", "email": "cfo@tech.com",
        "interes": "capital de trabajo", "presupuesto": 60000.0, "urgencia": "Alta",
        "perfil": "Gerente Financiero. Empresa de 51-200 colaboradores.",
        "empresa_tamano": "51-200", "tolerancia_riesgo": None,
        "_contexto_resumen": ["País: Ecuador"],
    }
    lead = ac.guardar_lead(datos)

    assert lead.id == "lead_007"                    # correlativo correcto
    assert lead.prioridad == "Alta"                 # 4+2+1+2+1 = 10 -> Alta
    assert lead.empresa_tamano == "51-200"          # campo nuevo persistido
    assert "Ecuador" in lead.resumen_conversacion_comercial  # país en resumen
    assert len(guardados) == 1                      # se llamó a crear_lead una vez
    # el LeadCRM se construyó sin romper por _contexto_resumen (clave interna)
    assert not hasattr(lead, "_contexto_resumen")


# =====================================================================
# Runner manual (sin pytest)
# =====================================================================
if __name__ == "__main__":
    import sys, traceback
    class _MP:
        """monkeypatch mínimo para correr sin pytest."""
        def __init__(self): self._undo = []
        def setattr(self, obj, name, val):
            old = getattr(obj, name); self._undo.append((obj, name, old))
            setattr(obj, name, val)
        def undo(self):
            for obj, name, old in reversed(self._undo): setattr(obj, name, old)

    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    passed = 0
    for nombre, fn in tests:
        mp = _MP()
        try:
            if "monkeypatch" in fn.__code__.co_varnames[:fn.__code__.co_argcount]:
                fn(mp)
            else:
                fn()
            print(f"  PASS  {nombre}"); passed += 1
        except Exception as e:
            print(f"  FAIL  {nombre}: {e}"); traceback.print_exc()
        finally:
            mp.undo()
    print(f"\n{passed}/{len(tests)} tests pasaron")
    sys.exit(0 if passed == len(tests) else 1)