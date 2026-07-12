from fastapi import APIRouter

router = APIRouter(prefix="/leads", tags=["HU1 - Calificación de Leads"])

@router.get("/ping")
def ping():
    return {"ok": True, "modulo": "HU1 - Calificación de Leads"}