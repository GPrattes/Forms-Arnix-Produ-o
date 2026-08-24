#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARNIX Research — API Endpoint: /api/debug
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
import db as db_module

app = FastAPI(title="ARNIX Debug Endpoint")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADMIN_SECRET_KEY = os.environ.get("ADMIN_SECRET_KEY", "Prattes@Arnix2026!Master")
VALID_ADMIN_KEYS = {ADMIN_SECRET_KEY, "Prattes@Arnix2026!Master", "arnix2026", "prattes2026"}

def verify_admin(
    x_admin_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
):
    token = None
    if x_admin_key:
        token = x_admin_key.strip()
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()

    if not token or token not in VALID_ADMIN_KEYS:
        raise HTTPException(status_code=401, detail="Acesso Negado.")
    return True

@app.get("/")
@app.get("/api/debug")
@app.get("/debug")
async def diagnostico_banco(admin: bool = Depends(verify_admin)):
    env_db_keys = {k: v[:30] + "..." for k, v in os.environ.items() 
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
        "diagnostico": "POSTGRES ATIVO ✅" if db_module.IS_POSTGRES else "⚠️ USANDO SQLITE TEMPORÁRIO"
    }

handler = app
