# shared/database.py
import json
import os
from typing import List, Optional
# Asumiendo que guardaron el esquema anterior en shared/schemas.py
from shared.schemas import LeadCRM

DB_FILE = "crm_database.json"

def _load_data() -> dict:
    """Función interna para leer el archivo JSON."""
    if not os.path.exists(DB_FILE):
        # Si el archivo no existe, inicializa con una estructura vacía
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump({"leads": []}, f, indent=4)
        return {"leads": []}
    
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"leads": []}

def _save_data(data: dict):
    """Función interna para guardar los cambios en el archivo JSON."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# =====================================================================
# FUNCIONES QUE USARÁ EL EQUIPO
# =====================================================================

def crear_lead(nuevo_lead: LeadCRM) -> LeadCRM:
    """
    USO: Compañero A (HU1)
    Recibe un objeto LeadCRM, lo guarda en el archivo y lo retorna.
    """
    data = _load_data()
    # Convertimos el objeto Pydantic a un diccionario normal de Python
    lead_dict = nuevo_lead.dict()
    
    # Evitar duplicados por ID o Email si es necesario
    data["leads"] = [l for l in data["leads"] if l["id"] != nuevo_lead.id and l["email"] != nuevo_lead.email]
    
    data["leads"].append(lead_dict)
    _save_data(data)
    return nuevo_lead

def obtener_lead_por_email(email: str) -> Optional[LeadCRM]:
    """
    USO: Compañero B (HU2)
    Busca un lead por su correo electrónico para poder actualizarlo.
    """
    data = _load_data()
    for lead_dict in data["leads"]:
        if lead_dict["email"] == email:
            return LeadCRM(**lead_dict) # Convierte el diccionario de vuelta a Objeto
    return None

def obtener_todos_los_leads() -> List[LeadCRM]:
    """
    USO: Compañero C (HU3)
    Retorna la lista completa de leads para mostrar en el Dashboard comercial.
    """
    data = _load_data()
    return [LeadCRM(**lead_dict) for lead_dict in data["leads"]]

def actualizar_lead(lead_actualizado: LeadCRM) -> bool:
    """
    USO: Compañero B y C (HU2 y HU3)
    Busca un lead por su ID y reemplaza sus datos con la nueva información.
    """
    data = _load_data()
    for i, lead_dict in enumerate(data["leads"]):
        if lead_dict["id"] == lead_actualizado.id:
            data["leads"][i] = lead_actualizado.dict()
            _save_data(data)
            return True
    return False