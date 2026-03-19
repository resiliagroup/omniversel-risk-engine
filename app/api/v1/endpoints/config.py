from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict
import json
import os

router = APIRouter()

K_MATRIX_FILE = "/tmp/k_matrix_override.json"

# hfer720.py has broken module-level imports — duplicate defaults here to avoid ImportError
_DEFAULT_K_MATRIX: Dict[str, Dict[str, float]] = {
    "HOSPITAL":     {"deprem": 2.8, "sel": 2.1, "natech": 3.5, "siber": 4.2},
    "INDUSTRIAL":   {"deprem": 3.2, "sel": 2.8, "natech": 4.8, "siber": 1.9},
    "BANK":         {"deprem": 1.8, "sel": 1.5, "natech": 2.0, "siber": 5.1},
    "MUNICIPALITY": {"deprem": 3.0, "sel": 2.5, "natech": 3.2, "siber": 3.8},
    "EDUCATION":    {"deprem": 2.5, "sel": 2.0, "natech": 1.8, "siber": 2.2},
    "HOTEL":        {"deprem": 2.2, "sel": 3.0, "natech": 2.5, "siber": 2.8},
}


class KMatrixPayload(BaseModel):
    sector_matrix: Dict[str, Dict[str, float]]


@router.get("/k-matrix")
async def get_k_matrix():
    if os.path.exists(K_MATRIX_FILE):
        with open(K_MATRIX_FILE) as f:
            return json.load(f)
    return {"sector_matrix": _DEFAULT_K_MATRIX}


@router.post("/k-matrix")
async def update_k_matrix(payload: KMatrixPayload):
    with open(K_MATRIX_FILE, "w") as f:
        json.dump({"sector_matrix": payload.sector_matrix}, f)
    return {"status": "ok", "saved": True}
