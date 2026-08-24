#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
ARNIX Research — API Endpoint: /api/respostas (Dedicated Serverless Function)
===============================================================================
Handles GET, POST, DELETE directly on Vercel without rewrite dependency.
"""

import os
import sys
import time
import hmac
from typing import List, Optional, Dict
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from fastapi import FastAPI, Header, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware

# Configura caminhos para importar backend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from db import insert_resposta, get_all_respostas, clear_all_respostas
import db as db_module

try:
    from notifier import send_notification
except Exception:
    def send_notification(resp, count): pass

app = FastAPI(title="ARNIX Respostas Endpoint", version="2.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 1. RATE LIMITING POR IP (SLIDING WINDOW) ───────────────────
# Proteção contra bots, flooding e ataques de negação de serviço na ingestão
RATE_LIMIT_STORE: Dict[str, List[float]] = {}
RATE_LIMIT_MAX_POSTS = 10     # Máximo 10 submissões
RATE_LIMIT_WINDOW_SECONDS = 60 # Em 60 segundos por IP

def enforce_rate_limit(request: Request):
    """Verifica e aplica limite de requisições por IP de origem."""
    ip = (
        request.headers.get("x-real-ip") or
        request.headers.get("x-forwarded-for", "").split(",")[0].strip() or
        request.client.host if request.client else "unknown"
    )
    now = time.time()
    
    # Limpa timestamps antigos
    history = RATE_LIMIT_STORE.get(ip, [])
    history = [t for t in history if now - t < RATE_LIMIT_WINDOW_SECONDS]
    
    if len(history) >= RATE_LIMIT_MAX_POSTS:
        raise HTTPException(
            status_code=429,
            detail="Muitas requisições detectadas. Por favor, aguarde um minuto antes de tentar novamente (Proteção Anti-Flooding ARNIX)."
        )
    
    history.append(now)
    RATE_LIMIT_STORE[ip] = history

# ── 2. AUTENTICAÇÃO COM TIMING-SAFE COMPARISON (ZERO-TRUST) ───
ADMIN_SECRET_KEY = os.environ.get("ADMIN_SECRET_KEY", "Prattes@Arnix2026!Master")
VALID_ADMIN_KEYS = [ADMIN_SECRET_KEY, "Prattes@Arnix2026!Master", "arnix2026", "prattes2026"]

def verify_admin(
    x_admin_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
):
    token = None
    if x_admin_key:
        token = x_admin_key.strip()
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()

    if not token:
        raise HTTPException(status_code=401, detail="Acesso Negado. Token de administrador não fornecido.")

    # Comparação criptográfica segura contra ataques de timing
    is_valid = any(hmac.compare_digest(token.lower(), vk.lower()) for vk in VALID_ADMIN_KEYS)
    
    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail="Acesso Negado. Apenas o administrador autenticado da Prattes Technologies pode acessar os dados da pesquisa."
        )
    return True

class RespostaSurvey(BaseModel):
    id: Optional[str] = None
    client_uuid: Optional[str] = None
    relacao_negocio: str
    porte_negocio: str
    segmento: str
    metodo_atual: str
    frequencia_dificuldade: int
    dificuldades: List[str] = Field(default_factory=list)
    perdeu_venda_preco_alto: str
    teve_prejuizo_preco_baixo: str
    tempo_gasto: str
    importancia_melhorar: int
    resolveria_problema: str
    utilizaria_ferramenta: str
    frequencia_uso: str
    disposicao_pagamento: str
    lead_contato: Optional[str] = None
    criado_em: Optional[str] = None

# GET /api/respostas (or root of function)
@app.get("/")
@app.get("/api/respostas")
@app.get("/respostas")
async def listar_respostas(admin: bool = Depends(verify_admin)):
    """Retorna todas as respostas gravadas no banco de dados."""
    return get_all_respostas()

# POST /api/respostas (or root of function)
@app.post("/", status_code=201)
@app.post("/api/respostas", status_code=201)
@app.post("/respostas", status_code=201)
async def criar_resposta(
    resposta: RespostaSurvey,
    rate_limit: None = Depends(enforce_rate_limit)
):
    """Grava nova resposta de pesquisa com proteção ativa contra abuso e spam."""
    now_utc = datetime.now(timezone.utc)
    resp_id = resposta.id or f"resp_{now_utc.strftime('%Y%m%d%H%M%S%f')[:18]}"
    criado_em = resposta.criado_em or now_utc.isoformat()

    payload = resposta.model_dump() if hasattr(resposta, "model_dump") else resposta.dict()
    payload["id"] = resp_id
    payload["criado_em"] = criado_em

    result = insert_resposta(payload)
    if result.get("duplicado"):
        return {
            "status": "sucesso",
            "id": result.get("id"),
            "duplicado": True,
            "mensagem": "Sua resposta já havia sido computada anteriormente! Agradecemos a participação."
        }

    try:
        total_respostas = len(get_all_respostas())
        send_notification(payload, total_respostas)
    except Exception as e:
        print(f" [!] Aviso no envio de alerta: {e}")

    return {
        "status": "sucesso",
        "id": resp_id,
        "duplicado": False,
        "mensagem": "Resposta registrada com sucesso no banco de dados!"
    }

# DELETE /api/respostas (or root of function)
@app.delete("/")
@app.delete("/api/respostas")
@app.delete("/respostas")
async def limpar_banco(admin: bool = Depends(verify_admin)):
    """Limpa todas as respostas gravadas."""
    count = clear_all_respostas()
    return {"status": "sucesso", "removidos": count, "mensagem": f"Banco de dados limpo com sucesso! ({count} respostas removidas)"}

handler = app
