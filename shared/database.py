# shared/database.py
import json
import os
from pathlib import Path
from typing import List, Optional

from shared.schemas import LeadCRM

BASE_DIR = Path(__file__).resolve().parents[1]
DB_FILE = BASE_DIR / "crm_database.json"


def _to_dict(model: LeadCRM) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _load_data() -> dict:
    """Lee el archivo JSON del CRM desde la ruta real del proyecto."""
    if not DB_FILE.exists():
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        with DB_FILE.open("w", encoding="utf-8") as f:
            json.dump({"leads": []}, f, indent=4, ensure_ascii=False)
        return {"leads": []}

    with DB_FILE.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return {"leads": []}

    if not isinstance(data, dict):
        return {"leads": []}
    data.setdefault("leads", [])
    return data


def _save_data(data: dict):
    """Guarda los cambios en el archivo JSON de forma segura."""
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = DB_FILE.with_suffix(DB_FILE.suffix + ".tmp")
    with temp_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    os.replace(temp_file, DB_FILE)


# =====================================================================
# FUNCIONES QUE USARÁ EL EQUIPO
# =====================================================================

def crear_lead(nuevo_lead: LeadCRM) -> LeadCRM:
    """
    USO: Compañero A (HU1)
    Recibe un objeto LeadCRM, lo guarda en el archivo y lo retorna.
    """
    data = _load_data()
    lead_dict = _to_dict(nuevo_lead)

    data["leads"] = [
        l for l in data["leads"] if l.get("id") != nuevo_lead.id and l.get("email") != nuevo_lead.email
    ]

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
        if lead_dict.get("email") == email:
            return LeadCRM(**lead_dict)
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
        if lead_dict.get("id") == lead_actualizado.id:
            data["leads"][i] = _to_dict(lead_actualizado)
            _save_data(data)
            return True
    return False