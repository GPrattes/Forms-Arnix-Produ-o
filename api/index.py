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
import hmac
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from fastapi import FastAPI, Response, Header, HTTPException, Depends, Request

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

from db import insert_resposta, get_all_respostas, clear_all_respostas
import db as db_module

try:
    from notifier import send_notification
except Exception:
    def send_notification(resp, count): pass

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

# ── MIDDLEWARE PURO ASGI PARA VERCEL (RESTAURA O PATH ORIGINAL) ──
class VercelPathFixMiddleware:
    """
    Quando a Vercel reescreve /api/(.*) -> /api/index.py, ela envia o caminho
    original no cabeçalho x-matched-path (ou x-vercel-matched-path).
    Este middleware atualiza scope['path'] antes do roteamento do FastAPI.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            headers = dict(scope.get("headers", []))
            matched_path = (
                headers.get(b"x-matched-path", b"").decode("utf-8", errors="ignore") or
                headers.get(b"x-vercel-matched-path", b"").decode("utf-8", errors="ignore") or
                headers.get(b"x-forwarded-uri", b"").decode("utf-8", errors="ignore") or
                headers.get(b"x-original-url", b"").decode("utf-8", errors="ignore")
            )
            if matched_path:
                clean_path = matched_path.split("?")[0]
                scope["path"] = clean_path
                scope["raw_path"] = clean_path.encode("utf-8")
        await self.app(scope, receive, send)

app.add_middleware(VercelPathFixMiddleware)

# ── MIDDLEWARE DE DIAGNÓSTICO (Vercel Path Logging) ────────────
@app.middleware("http")
async def vercel_request_logger(request: Request, call_next):
    """Log detalhado de cada requisição para diagnosticar roteamento Vercel."""
    path = request.url.path
    method = request.method
    print(f" [REQ] {method} {path} | scope_path={request.scope.get('path')}")
    response = await call_next(request)
    print(f" [RES] {method} {path} -> {response.status_code}")
    return response

@app.get("/api")
@app.get("/api/")
@app.get("/api/index")
@app.get("/api/index.py")
async def api_root_info(request: Request):
    """Retorna informações, status da API e diagnóstico de cabeçalhos."""
    hdrs = {k: v for k, v in request.headers.items()}
    return {
        "status": "online",
        "service": "ARNIX Research Serverless API",
        "is_postgres": db_module.IS_POSTGRES,
        "is_vercel": db_module.IS_VERCEL,
        "path": request.url.path,
        "scope_path": request.scope.get("path"),
        "raw_path": str(request.scope.get("raw_path")),
        "headers": hdrs,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ── ROTAS DE DIAGNÓSTICO PÚBLICAS ──────────────────────────────
@app.get("/api/health")
@app.get("/api/index.py/health")
async def health_check():
    """Endpoint público para verificar se a API está funcionando."""
    return {
        "status": "ok",
        "is_postgres": db_module.IS_POSTGRES,
        "is_vercel": db_module.IS_VERCEL,
        "db_url_found": bool(db_module.DB_URL),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/test-get")
@app.get("/api/index.py/test-get")
async def test_get_route():
    """Rota GET de teste sem nenhuma dependência/autenticação."""
    return {"method": "GET", "status": "working", "message": "GET route is functional!"}

# ── GUARDA DE SEGURANÇA DO ADMINISTRADOR ───────────────────────
def get_admin_secret_key() -> str:
    return os.environ.get("ADMIN_SECRET_KEY", "").strip()

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

    admin_key = get_admin_secret_key()
    if not token or not admin_key or not hmac.compare_digest(token, admin_key):
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

@app.get("/sobre", include_in_schema=False)
@app.get("/sobre.html", include_in_schema=False)
async def serve_sobre():
    sobre_path = os.path.join(FRONTEND_DIR, "sobre.html")
    if not os.path.exists(sobre_path):
        sobre_path = os.path.join(BASE_DIR, "sobre.html")
    return FileResponse(sobre_path)

@app.get("/fundador", include_in_schema=False)
@app.get("/fundador.html", include_in_schema=False)
async def serve_fundador():
    fundador_path = os.path.join(FRONTEND_DIR, "fundador.html")
    if not os.path.exists(fundador_path):
        fundador_path = os.path.join(BASE_DIR, "fundador.html")
    return FileResponse(fundador_path)

@app.get("/obrigado", include_in_schema=False)
@app.get("/obrigado.html", include_in_schema=False)
async def serve_obrigado():
    obrigado_path = os.path.join(FRONTEND_DIR, "obrigado.html")
    if not os.path.exists(obrigado_path):
        obrigado_path = os.path.join(BASE_DIR, "obrigado.html")
    return FileResponse(obrigado_path)

@app.get("/politica-privacidade", include_in_schema=False)
@app.get("/politica-privacidade.html", include_in_schema=False)
async def serve_privacidade():
    priv_path = os.path.join(FRONTEND_DIR, "politica-privacidade.html")
    if not os.path.exists(priv_path):
        priv_path = os.path.join(BASE_DIR, "politica-privacidade.html")
    return FileResponse(priv_path)

@app.get("/termos-uso", include_in_schema=False)
@app.get("/termos-uso.html", include_in_schema=False)
async def serve_termos():
    termos_path = os.path.join(FRONTEND_DIR, "termos-uso.html")
    if not os.path.exists(termos_path):
        termos_path = os.path.join(BASE_DIR, "termos-uso.html")
    return FileResponse(termos_path)

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
    client_uuid: Optional[str] = None
    relacao_negocio: str
    porte_negocio: str
    segmento: str
    metodo_atual: str
    ferramenta_especifica: Optional[str] = None
    frequencia_dificuldade: int
    dificuldades: List[str] = Field(default_factory=list)
    perdeu_venda_preco_alto: str
    teve_prejuizo_preco_baixo: str
    tempo_gasto: str
    importancia_melhorar: int
    resolveria_problema: str
    fatores_substituicao: List[str] = Field(default_factory=list)
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
    admin_key = get_admin_secret_key()
    if admin_key and req.password and hmac.compare_digest(req.password.strip(), admin_key):
        return {"status": "autenticado", "token": req.password.strip(), "usuario": "Rafael Prattes (Admin)"}
    raise HTTPException(status_code=401, detail="Chave Mestre de Administrador Incorreta.")


# ── ROTA DE DIAGNÓSTICO DO BANCO (🔒 EXCLUSIVO DO ADMINISTRADOR) ──
@app.get("/api/debug", dependencies=[Depends(verify_admin_token)])
@app.get("/api/index.py/debug", dependencies=[Depends(verify_admin_token)])
async def diagnostico_banco():
    """Retorna diagnóstico completo do estado de conexão do banco de dados."""
    import os as _os
    env_db_keys = {k: v[:30] + "..." for k, v in _os.environ.items() 
                   if any(x in k.upper() for x in ["POSTGRES", "DATABASE", "ARMAZENAR", "NEON"])}
    
    pg_test = "NÃO TESTADO"
    pg_count = 0
    if db_module.IS_POSTGRES:
        try:
            conn = db_module.get_postgres_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as total FROM respostas_pesquisa;")
            row = cur.fetchone()
            pg_count = row["total"] if row else 0
            cur.close()
            conn.close()
            pg_test = f"CONECTADO - {pg_count} registros"
        except Exception as e:
            pg_test = f"ERRO: {str(e)}"
    
    sqlite_test = "NÃO TESTADO"
    sqlite_count = 0
    try:
        import sqlite3
        sconn = sqlite3.connect(db_module.SQLITE_DB_PATH)
        scur = sconn.cursor()
        scur.execute("SELECT COUNT(*) FROM respostas_pesquisa;")
        sqlite_count = scur.fetchone()[0]
        sconn.close()
        sqlite_test = f"CONECTADO - {sqlite_count} registros"
    except Exception as e:
        sqlite_test = f"ERRO: {str(e)}"
    
    all_data = get_all_respostas()
    
    return {
        "is_postgres": db_module.IS_POSTGRES,
        "is_vercel": db_module.IS_VERCEL,
        "db_url_detected": bool(db_module.DB_URL),
        "db_url_preview": db_module.DB_URL[:40] + "..." if db_module.DB_URL else "VAZIO",
        "env_db_vars": env_db_keys,
        "postgres_test": pg_test,
        "postgres_count": pg_count,
        "sqlite_path": db_module.SQLITE_DB_PATH,
        "sqlite_test": sqlite_test,
        "sqlite_count": sqlite_count,
        "get_all_respostas_count": len(all_data),
        "diagnostico": "POSTGRES ATIVO ✅" if db_module.IS_POSTGRES else "⚠️ USANDO SQLITE TEMPORÁRIO (dados não persistem entre invocações Serverless!)"
    }

# ── 1. INGESTÃO PÚBLICA (ABERTO PARA O PÚBLICO COM ANTI-DUPLICAÇÃO)
@app.post("/api/respostas", status_code=201)
@app.post("/respostas", status_code=201)
@app.post("/api/index.py/respostas", status_code=201)
@app.post("/api/index/respostas", status_code=201)
@app.post("/api/index.py", status_code=201)
@app.post("/api/index", status_code=201)
async def criar_resposta_serverless(resposta: RespostaSurvey):
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

    # Dispara notificação por e-mail com a contagem total de respondentes
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

# ── 2. CONSULTA DO BANCO (🔒 EXCLUSIVO DO ADMINISTRADOR) ──────
@app.get("/api/respostas", dependencies=[Depends(verify_admin_token)])
@app.get("/respostas", dependencies=[Depends(verify_admin_token)])
@app.get("/api/index.py/respostas", dependencies=[Depends(verify_admin_token)])
@app.get("/api/index/respostas", dependencies=[Depends(verify_admin_token)])
async def listar_respostas_serverless():
    return get_all_respostas()

# ── 2.1 LIMPEZA TOTAL DO BANCO (🔒 EXCLUSIVO DO ADMINISTRADOR) ──
@app.delete("/api/respostas", dependencies=[Depends(verify_admin_token)])
@app.delete("/respostas", dependencies=[Depends(verify_admin_token)])
@app.delete("/api/index.py/respostas", dependencies=[Depends(verify_admin_token)])
@app.post("/api/admin/limpar-banco", dependencies=[Depends(verify_admin_token)])
@app.post("/admin/limpar-banco", dependencies=[Depends(verify_admin_token)])
async def limpar_banco_serverless():
    """Remove todas as respostas gravadas (Postgres ou SQLite)."""
    count = clear_all_respostas()
    return {"status": "sucesso", "removidos": count, "mensagem": f"Banco de dados limpo com sucesso! ({count} respostas removidas)"}

# ── 3. MÉTRICAS ESTATÍSTICAS (🔒 EXCLUSIVO DO ADMINISTRADOR) ──
@app.get("/api/metricas", dependencies=[Depends(verify_admin_token)])
@app.get("/metricas", dependencies=[Depends(verify_admin_token)])
@app.get("/api/index.py/metricas", dependencies=[Depends(verify_admin_token)])
@app.get("/api/index/metricas", dependencies=[Depends(verify_admin_token)])
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

# ══════════════════════════════════════════════════════════════
# VERCEL PYTHON RUNTIME HANDLER EXPORT
# A Vercel exige que a variável 'app' ou 'handler' esteja exportada
# no nível do módulo para rotear TODOS os métodos HTTP (GET, POST, DELETE).
# ══════════════════════════════════════════════════════════════
handler = app
