from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict
import json
import os

router = APIRouter()

K_MATRIX_FILE = "/tmp/k_matrix_override.json"


class KMatrixPayload(BaseModel):
    sector_matrix: Dict[str, Dict[str, float]]


@router.get("/k-matrix")
async def get_k_matrix():
    if os.path.exists(K_MATRIX_FILE):
        with open(K_MATRIX_FILE) as f:
            return json.load(f)
    from app.services.risk.hfer720 import DEFAULT_K_MATRIX
    return {"sector_matrix": DEFAULT_K_MATRIX}


@router.post("/k-matrix")
async def update_k_matrix(payload: KMatrixPayload):
    with open(K_MATRIX_FILE, "w") as f:
        json.dump({"sector_matrix": payload.sector_matrix}, f)
    return {"status": "ok", "saved": True}
