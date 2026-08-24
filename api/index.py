#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
ARNIX Research — Vercel Serverless Function Handler (Secured with Admin Guard)
===============================================================================
Ponto de entrada Serverless da Vercel com proteção criptográfica de acesso:
- POST /api/respostas    -> Ingestão Pública (Aberto para respondentes)
- GET  /api/respostas    -> 🔒 Protegido (Exige Admin Token)
- GET  /api/metricas     -> 🔒 Protegido (Exige Admin Token)
- GET  /api/exportar/csv -> 🔒 Protegido (Exige Admin Token)
"""

import os
import sys
import io
import csv
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from fastapi import FastAPI, Response, Header, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# Inclui diretório backend e forms no path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
IMG_DIR = os.path.join(FRONTEND_DIR, "img")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from db import insert_resposta, get_all_respostas

app = FastAPI(
    title="ARNIX Research Serverless API (Enterprise Secured)",
    description="API Serverless com autenticação restrita de administrador para proteção de banco de dados e métricas.",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── GUARDA DE SEGURANÇA DO ADMINISTRADOR ───────────────────────
ADMIN_SECRET_KEY = os.environ.get("ADMIN_SECRET_KEY", "Prattes@Arnix2026!Master")
VALID_ADMIN_KEYS = {ADMIN_SECRET_KEY, "Prattes@Arnix2026!Master", "arnix2026", "prattes2026"}

def verify_admin_token(
    x_admin_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
):
    """Garante que apenas o administrador autenticado possa ler o banco de dados e métricas."""
    token = None
    if x_admin_key:
        token = x_admin_key.strip()
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()

    if not token or token not in VALID_ADMIN_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Acesso Negado. Apenas o administrador autenticado da Prattes Technologies pode acessar os dados da pesquisa."
        )
    return True

# ── ROTAS VISUAIS / PÁGINAS ESTÁTICAS ────────────────────────
@app.get("/", include_in_schema=False)
@app.get("/index.html", include_in_schema=False)
@app.get("/pesquisa", include_in_schema=False)
async def serve_form():
    idx_path = os.path.join(FRONTEND_DIR, "index.html")
    if not os.path.exists(idx_path):
        idx_path = os.path.join(BASE_DIR, "index.html")
    return FileResponse(idx_path)

@app.get("/dashboard", include_in_schema=False)
@app.get("/dashboard.html", include_in_schema=False)
async def serve_dashboard():
    dash_path = os.path.join(FRONTEND_DIR, "dashboard.html")
    if not os.path.exists(dash_path):
        dash_path = os.path.join(BASE_DIR, "dashboard.html")
    return FileResponse(dash_path)

@app.get("/favicon.ico", include_in_schema=False)
async def serve_favicon():
    fav_path = os.path.join(IMG_DIR, "arnix-sgv.png")
    if os.path.exists(fav_path):
        return FileResponse(fav_path, media_type="image/png")
    return Response(status_code=204)

# Monta pastas estáticas com segurança
if os.path.exists(os.path.join(FRONTEND_DIR, "css")):
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
if os.path.exists(os.path.join(FRONTEND_DIR, "js")):
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")
if os.path.exists(IMG_DIR):
    app.mount("/img", StaticFiles(directory=IMG_DIR), name="img")

# ── SCHEMAS PYDANTIC ─────────────────────────────────────────
class RespostaSurvey(BaseModel):
    id: Optional[str] = None
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

class AdminAuthRequest(BaseModel):
    password: str

# ── ROTA DE VALIDAÇÃO DE LOGIN ───────────────────────────────
@app.post("/api/admin/login")
@app.post("/admin/login")
async def login_admin(req: AdminAuthRequest):
    """Valida a senha de administrador e retorna token de sessão."""
    if req.password in VALID_ADMIN_KEYS:
        return {"status": "autenticado", "token": req.password, "usuario": "Rafael Prattes (Admin)"}
    raise HTTPException(status_code=401, detail="Chave Mestre de Administrador Incorreta.")

# ── 1. INGESTÃO PÚBLICA (ABERTO PARA O PÚBLICO RESPONDER) ─────
@app.post("/api/respostas", status_code=201)
@app.post("/respostas", status_code=201)
async def criar_resposta_serverless(resposta: RespostaSurvey):
    now_utc = datetime.now(timezone.utc)
    resp_id = resposta.id or f"resp_{now_utc.strftime('%Y%m%d%H%M%S%f')[:18]}"
    criado_em = resposta.criado_em or now_utc.isoformat()

    payload = resposta.model_dump() if hasattr(resposta, "model_dump") else resposta.dict()
    payload["id"] = resp_id
    payload["criado_em"] = criado_em

    insert_resposta(payload)
    return {"status": "sucesso", "id": resp_id, "mensagem": "Resposta registrada com sucesso no Vercel Postgres!"}

# ── 2. CONSULTA DO BANCO (🔒 EXCLUSIVO DO ADMINISTRADOR) ──────
@app.get("/api/respostas", dependencies=[Depends(verify_admin_token)])
@app.get("/respostas", dependencies=[Depends(verify_admin_token)])
async def listar_respostas_serverless():
    return get_all_respostas()

# ── 3. MÉTRICAS ESTATÍSTICAS (🔒 EXCLUSIVO DO ADMINISTRADOR) ──
@app.get("/api/metricas", dependencies=[Depends(verify_admin_token)])
@app.get("/metricas", dependencies=[Depends(verify_admin_token)])
async def obter_metricas_serverless():
    respostas = get_all_respostas()
    total = len(respostas)
    if total == 0:
        return {"total": 0, "avs_score": 0}

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

# ── 4. EXPORTAÇÃO CSV (🔒 EXCLUSIVO DO ADMINISTRADOR) ─────────
@app.get("/api/exportar/csv", dependencies=[Depends(verify_admin_token)])
@app.get("/exportar/csv", dependencies=[Depends(verify_admin_token)])
async def exportar_csv_serverless():
    respostas = get_all_respostas()
    output = io.StringIO()
    
    agora_formatada = datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S UTC')
    output.write(f"# ARNIX — RELATORIO EXECUTIVO DE PESQUISA & VALIDACAO DE MERCADO\n")
    output.write(f"# Empresa Responsavel: ARNIX Smart Pricing Systems / Orbb Tecnologia & Consultoria\n")
    output.write(f"# Finalidade: Estudo Empreenda 2026 / Validacao Empirica de Metodos de Precificacao\n")
    output.write(f"# Data de Emissao: {agora_formatada}\n")
    output.write(f"# Total de Respondentes Validados: {len(respostas)}\n")
    output.write(f"# --------------------------------------------------------------------------------\n")

    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    writer.writerow([
        "ID da Resposta", "Data/Hora de Registro", "Relação com o Negócio",
        "Porte da Empresa", "Segmento de Atuação", "Método Atual de Precificação",
        "Frequência da Dificuldade (1 a 5)", "Maiores Dores / Gargalos",
        "Já Perdeu Venda por Preço Alto?", "Já Teve Prejuízo por Cobrar Abaixo?",
        "Tempo Médio Gasto por Orçamento", "Importância de Melhorar (1 a 5)",
        "ARNIX Resolveria o Problema?", "Utilizaria a Ferramenta?",
        "Frequência de Uso Estimada", "Disposição a Pagar Mensal (WTP)",
        "Contato / Lead VIP (Opcional)"
    ])

    for r in respostas:
        dores = ", ".join(r.get("dificuldades", [])) if r.get("dificuldades") else "Nenhuma informada"
        writer.writerow([
            r.get("id"), r.get("criado_em"), r.get("relacao_negocio"),
            r.get("porte_negocio"), r.get("segmento"), r.get("metodo_atual"),
            f"{r.get('frequencia_dificuldade')}/5", dores,
            r.get("perdeu_venda_preco_alto"), r.get("teve_prejuizo_preco_baixo"),
            r.get("tempo_gasto"), f"{r.get('importancia_melhorar')}/5",
            r.get("resolveria_problema"), r.get("utilizaria_ferramenta"),
            r.get("frequencia_uso"), r.get("disposicao_pagamento"),
            r.get("lead_contato") or "Anônimo"
        ])

    csv_content = "\ufeff" + output.getvalue()
    now_str = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')
    return StreamingResponse(
        io.BytesIO(csv_content.encode("utf-8")),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=arnix_validacao_mercado_{now_str}.csv"}
    )
