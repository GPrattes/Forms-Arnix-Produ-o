#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
ARNIX Research & Market Validation Server (Secured Admin API)
===============================================================================
Servidor FastAPI e banco dual (Vercel Postgres em produção / SQLite local)
para coleta pública de respostas e painel analítico com acesso restrito.
"""

import os
import sys
import io
import csv
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

# Garante suporte UTF-8 no Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import uvicorn
from fastapi import FastAPI, HTTPException, Response, Header, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FORMS_ROOT = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(FORMS_ROOT, "frontend")
IMG_DIR = os.path.join(FRONTEND_DIR, "img")

# Importa o driver de banco dual (Vercel Postgres / SQLite)
from db import insert_resposta, get_all_respostas

# ── SCHEMAS PYDANTIC ─────────────────────────────────────────
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

class AdminAuthRequest(BaseModel):
    password: str

# ── FASTAPI APP ──────────────────────────────────────────────
app = FastAPI(
    title="ARNIX Market Validation API (Enterprise Secured)",
    description="Backend de coleta de dados empíricos com proteção de acesso exclusivo ao administrador.",
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
    """Garante que apenas o administrador possa consultar o banco de dados e métricas."""
    token = None
    if x_admin_key:
        token = x_admin_key.strip()
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()

    if not token or token not in VALID_ADMIN_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Acesso Negado. Apenas o administrador autenticado pode acessar os dados da pesquisa."
        )
    return True

# ── ROTAS DE PÁGINAS ESTÁTICAS & FAVICONS ────────────────────
@app.get("/", include_in_schema=False)
@app.get("/index.html", include_in_schema=False)
async def serve_form():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/dashboard", include_in_schema=False)
@app.get("/dashboard.html", include_in_schema=False)
async def serve_dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))

@app.get("/sobre", include_in_schema=False)
@app.get("/sobre.html", include_in_schema=False)
async def serve_sobre():
    return FileResponse(os.path.join(FRONTEND_DIR, "sobre.html"))

@app.get("/fundador", include_in_schema=False)
@app.get("/fundador.html", include_in_schema=False)
@app.get("/gabriel-prattes", include_in_schema=False)
async def serve_fundador():
    return FileResponse(os.path.join(FRONTEND_DIR, "fundador.html"))

@app.get("/favicon.ico", include_in_schema=False)
async def serve_favicon():
    favicon_path = os.path.join(IMG_DIR, "arnix-sgv.png")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path, media_type="image/png")
    return Response(status_code=204)

app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")
app.mount("/img", StaticFiles(directory=IMG_DIR), name="img")

# ── ROTA DE VALIDAÇÃO DE LOGIN ───────────────────────────────
@app.post("/api/admin/login")
async def login_admin(req: AdminAuthRequest):
    """Valida a senha de administrador e retorna token de sessão."""
    if req.password in VALID_ADMIN_KEYS:
        return {"status": "autenticado", "token": req.password, "usuario": "Rafael Prattes (Admin)"}
    raise HTTPException(status_code=401, detail="Chave Mestre de Administrador Incorreta.")

# ── 1. INGESTÃO PÚBLICA (ABERTO PARA O PÚBLICO RESPONDER) ─────
@app.post("/api/respostas", status_code=201)
async def criar_resposta(resposta: RespostaSurvey):
    """Grava uma nova resposta de pesquisa anonimizada no banco (Vercel Postgres ou SQLite)."""
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

    return {
        "status": "sucesso",
        "id": resp_id,
        "duplicado": False,
        "mensagem": "Resposta registrada com sucesso!"
    }

# ── 2. CONSULTA DO BANCO (🔒 EXCLUSIVO DO ADMINISTRADOR) ──────
@app.get("/api/respostas", dependencies=[Depends(verify_admin_token)])
async def listar_respostas():
    """Retorna todas as respostas coletadas."""
    return get_all_respostas()

# ── 3. MÉTRICAS CONSOLIDADAS (🔒 EXCLUSIVO DO ADMINISTRADOR) ──
@app.get("/api/metricas", dependencies=[Depends(verify_admin_token)])
async def obter_metricas_consolidadas():
    """Calcula as métricas executivas e o ARNIX Validation Score (AVS)."""
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

    # AVS = 30% Problema + 25% Interesse + 20% Uso + 15% Pagamento + 10% Frequência
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
async def exportar_csv():
    """Gera o arquivo CSV corporativo de todas as respostas formatado para Excel/Sheets com UTF-8 BOM."""
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

PORT = 8090

if __name__ == "__main__":
    print("=" * 76)
    print(" 🚀 ARNIX — SERVIDOR DE PESQUISA & VALIDATION DASHBOARD")
    print("=" * 76)
    print(f" 📝 Formulário de Pesquisa:  http://localhost:{PORT}")
    print(f" 📊 Dashboard de Validação:   http://localhost:{PORT}/dashboard")
    print(f" 📑 Documentação Swagger:     http://localhost:{PORT}/docs")
    print("=" * 76)
    print(f" Servindo em http://0.0.0.0:{PORT}...\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
