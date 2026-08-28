#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARNIX Research — API Endpoint: /api/metricas
"""
import os
import sys
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from db import get_all_respostas

app = FastAPI(title="ARNIX Metricas Endpoint")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import hmac

def get_admin_secret_key() -> str:
    return os.environ.get("ADMIN_SECRET_KEY", "").strip()

def verify_admin(
    x_admin_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
):
    token = None
    if isinstance(x_admin_key, str) and x_admin_key.strip():
        token = x_admin_key.strip()
    elif isinstance(authorization, str) and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()

    admin_key = get_admin_secret_key()
    if not token or not admin_key or not hmac.compare_digest(token, admin_key):
        raise HTTPException(
            status_code=401,
            detail="Acesso Negado. Autenticação de administrador obrigatória."
        )
    return True



@app.get("/")
@app.get("/api/metricas")
@app.get("/metricas")
async def obter_metricas(admin: bool = Depends(verify_admin)):
    respostas = get_all_respostas()
    total = len(respostas)
    if total == 0:
        return {"total_respondentes": 0, "avs_score": 0}

    count_problema = sum(1 for r in respostas if r.get("frequencia_dificuldade", 0) >= 3)
    pct_problema = round((count_problema / total) * 100)

    count_interesse = sum(1 for r in respostas if "bastante" in (r.get("resolveria_problema") or "") or "parcialmente" in (r.get("resolveria_problema") or ""))
    pct_interesse = round((count_interesse / total) * 100)

    count_uso = sum(1 for r in respostas if "certeza" in (r.get("utilizaria_ferramenta") or "") or "Provavelmente" in (r.get("utilizaria_ferramenta") or ""))
    pct_uso = round((count_uso / total) * 100)

    count_pagamento = sum(1 for r in respostas if r.get("disposicao_pagamento") and "Gratuito" not in r.get("disposicao_pagamento"))
    pct_pagamento = round((count_pagamento / total) * 100)

    sum_imp = sum(r.get("importancia_melhorar", 3) for r in respostas)
    pct_frequencia = round((sum_imp / (total * 5)) * 100)

    avs_score = round(
        (0.30 * pct_problema) +
        (0.25 * pct_interesse) +
        (0.20 * pct_uso) +
        (0.15 * pct_pagamento) +
        (0.10 * pct_frequencia)
    )

    return {
        "total_respondentes": total,
        "avs_score": avs_score,
        "avs_status": "Strong Market Signal" if avs_score >= 75 else "Moderate Market Signal",
        "pct_problema": pct_problema,
        "pct_interesse_arnix": pct_interesse,
        "pct_intencao_uso": pct_uso,
        "pct_disposicao_pagamento": pct_pagamento,
        "preco_medio_referencia": "R$ 49,90"
    }

handler = app
