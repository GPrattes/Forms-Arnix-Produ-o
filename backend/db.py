#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
ARNIX Research — Database Engine (Vercel Postgres & SQLite Serverless Driver)
===============================================================================
Gerencia a persistência de respostas suportando:
1. Vercel Postgres / Supabase / Neon (Nuvem em Produção)
2. SQLite seguro com fallback /tmp para ambientes Serverless / Read-Only
"""

import os
import sys
import json
import sqlite3
from typing import List, Dict, Any, Optional

DB_URL = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL") or ""

# Normaliza postgres:// para postgresql:// para drivers modernos
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

IS_POSTGRES = bool(DB_URL and ("postgresql" in DB_URL or "postgres" in DB_URL))

# Determina caminho seguro para SQLite (usa /tmp no ambiente Serverless da Vercel)
IS_VERCEL = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

if IS_VERCEL:
    SQLITE_DB_PATH = "/tmp/arnix_respostas.db"
else:
    LOCAL_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    try:
        os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
        SQLITE_DB_PATH = os.path.join(LOCAL_DATA_DIR, "respostas.db")
    except Exception:
        SQLITE_DB_PATH = "/tmp/arnix_respostas.db"

def get_postgres_connection():
    import psycopg2
    from psycopg2.extras import RealDictCursor
    return psycopg2.connect(DB_URL, sslmode="require", cursor_factory=RealDictCursor)

def init_database():
    """Cria a tabela de respostas caso não exista (PostgreSQL ou SQLite)."""
    if IS_POSTGRES:
        try:
            conn = get_postgres_connection()
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS respostas_pesquisa (
                id VARCHAR(64) PRIMARY KEY,
                relacao_negocio VARCHAR(100),
                porte_negocio VARCHAR(100),
                segmento VARCHAR(100),
                metodo_atual VARCHAR(100),
                frequencia_dificuldade INT,
                dificuldades TEXT,
                perdeu_venda_preco_alto VARCHAR(20),
                teve_prejuizo_preco_baixo VARCHAR(20),
                tempo_gasto VARCHAR(50),
                importancia_melhorar INT,
                resolveria_problema VARCHAR(100),
                utilizaria_ferramenta VARCHAR(100),
                frequencia_uso VARCHAR(100),
                disposicao_pagamento VARCHAR(100),
                lead_contato VARCHAR(255),
                criado_em VARCHAR(50)
            );
            """)
            conn.commit()
            cursor.close()
            conn.close()
            print(" [OK] Tabela no Vercel Postgres conectada com sucesso!")
        except Exception as e:
            print(f" [!] Aviso ao inicializar Vercel Postgres: {e}")
    else:
        try:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS respostas_pesquisa (
                id TEXT PRIMARY KEY,
                relacao_negocio TEXT,
                porte_negocio TEXT,
                segmento TEXT,
                metodo_atual TEXT,
                frequencia_dificuldade INTEGER,
                dificuldades TEXT,
                perdeu_venda_preco_alto TEXT,
                teve_prejuizo_preco_baixo TEXT,
                tempo_gasto TEXT,
                importancia_melhorar INTEGER,
                resolveria_problema TEXT,
                utilizaria_ferramenta TEXT,
                frequencia_uso TEXT,
                disposicao_pagamento TEXT,
                lead_contato TEXT,
                criado_em TEXT
            );
            """)
            conn.commit()
            conn.close()
            print(f" [OK] Banco de Dados SQLite verificado em {SQLITE_DB_PATH}")
        except Exception as e:
            print(f" [!] Aviso ao inicializar SQLite: {e}")

try:
    init_database()
except Exception as e:
    print(f" [!] Aviso silencioso na inicialização do banco: {e}")

def insert_resposta(resp: Dict[str, Any]) -> str:
    """Insere uma resposta no banco (PostgreSQL na Vercel ou SQLite local)."""
    resp_id = resp.get("id")
    dificuldades_json = json.dumps(resp.get("dificuldades", []), ensure_ascii=False)

    if IS_POSTGRES:
        try:
            conn = get_postgres_connection()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO respostas_pesquisa (
                id, relacao_negocio, porte_negocio, segmento, metodo_atual,
                frequencia_dificuldade, dificuldades, perdeu_venda_preco_alto,
                teve_prejuizo_preco_baixo, tempo_gasto, importancia_melhorar,
                resolveria_problema, utilizaria_ferramenta, frequencia_uso,
                disposicao_pagamento, lead_contato, criado_em
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                resp_id, resp.get("relacao_negocio"), resp.get("porte_negocio"), resp.get("segmento"),
                resp.get("metodo_atual"), resp.get("frequencia_dificuldade"), dificuldades_json,
                resp.get("perdeu_venda_preco_alto"), resp.get("teve_prejuizo_preco_baixo"),
                resp.get("tempo_gasto"), resp.get("importancia_melhorar"), resp.get("resolveria_problema"),
                resp.get("utilizaria_ferramenta"), resp.get("frequencia_uso"),
                resp.get("disposicao_pagamento"), resp.get("lead_contato"), resp.get("criado_em")
            ))
            conn.commit()
            cursor.close()
            conn.close()
            return resp_id
        except Exception as e:
            print(f" [!] Erro ao gravar no Postgres: {e}")

    # Fallback SQLite
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO respostas_pesquisa (
            id, relacao_negocio, porte_negocio, segmento, metodo_atual,
            frequencia_dificuldade, dificuldades, perdeu_venda_preco_alto,
            teve_prejuizo_preco_baixo, tempo_gasto, importancia_melhorar,
            resolveria_problema, utilizaria_ferramenta, frequencia_uso,
            disposicao_pagamento, lead_contato, criado_em
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            resp_id, resp.get("relacao_negocio"), resp.get("porte_negocio"), resp.get("segmento"),
            resp.get("metodo_atual"), resp.get("frequencia_dificuldade"), dificuldades_json,
            resp.get("perdeu_venda_preco_alto"), resp.get("teve_prejuizo_preco_baixo"),
            resp.get("tempo_gasto"), resp.get("importancia_melhorar"), resp.get("resolveria_problema"),
            resp.get("utilizaria_ferramenta"), resp.get("frequencia_uso"),
            resp.get("disposicao_pagamento"), resp.get("lead_contato"), resp.get("criado_em")
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f" [!] Erro ao gravar no SQLite: {e}")

    return resp_id

def get_all_respostas() -> List[Dict[str, Any]]:
    """Recupera todas as respostas gravadas."""
    respostas = []
    if IS_POSTGRES:
        try:
            conn = get_postgres_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM respostas_pesquisa ORDER BY criado_em DESC;")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            for r in rows:
                dificuldades_list = []
                try:
                    dificuldades_list = json.loads(r["dificuldades"]) if r["dificuldades"] else []
                except Exception:
                    pass

                respostas.append({
                    "id": r["id"],
                    "relacao_negocio": r["relacao_negocio"] or "",
                    "porte_negocio": r["porte_negocio"] or "",
                    "segmento": r["segmento"] or "",
                    "metodo_atual": r["metodo_atual"] or "",
                    "frequencia_dificuldade": r["frequencia_dificuldade"] or 3,
                    "dificuldades": dificuldades_list,
                    "perdeu_venda_preco_alto": r["perdeu_venda_preco_alto"] or "",
                    "teve_prejuizo_preco_baixo": r["teve_prejuizo_preco_baixo"] or "",
                    "tempo_gasto": r["tempo_gasto"] or "",
                    "importancia_melhorar": r["importancia_melhorar"] or 3,
                    "resolveria_problema": r["resolveria_problema"] or "",
                    "utilizaria_ferramenta": r["utilizaria_ferramenta"] or "",
                    "frequencia_uso": r["frequencia_uso"] or "",
                    "disposicao_pagamento": r["disposicao_pagamento"] or "",
                    "lead_contato": r["lead_contato"],
                    "criado_em": r["criado_em"]
                })
            return respostas
        except Exception as e:
            print(f" [!] Erro ao ler Postgres: {e}")

    # Fallback SQLite
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM respostas_pesquisa ORDER BY criado_em DESC")
        rows = cursor.fetchall()
        conn.close()

        for r in rows:
            dificuldades_list = []
            try:
                dificuldades_list = json.loads(r["dificuldades"]) if r["dificuldades"] else []
            except Exception:
                pass

            respostas.append({
                "id": r["id"],
                "relacao_negocio": r["relacao_negocio"] or "",
                "porte_negocio": r["porte_negocio"] or "",
                "segmento": r["segmento"] or "",
                "metodo_atual": r["metodo_atual"] or "",
                "frequencia_dificuldade": r["frequencia_dificuldade"] or 3,
                "dificuldades": dificuldades_list,
                "perdeu_venda_preco_alto": r["perdeu_venda_preco_alto"] or "",
                "teve_prejuizo_preco_baixo": r["teve_prejuizo_preco_baixo"] or "",
                "tempo_gasto": r["tempo_gasto"] or "",
                "importancia_melhorar": r["importancia_melhorar"] or 3,
                "resolveria_problema": r["resolveria_problema"] or "",
                "utilizaria_ferramenta": r["utilizaria_ferramenta"] or "",
                "frequencia_uso": r["frequencia_uso"] or "",
                "disposicao_pagamento": r["disposicao_pagamento"] or "",
                "lead_contato": r["lead_contato"],
                "criado_em": r["criado_em"]
            })
    except Exception as e:
        print(f" [!] Erro ao ler SQLite: {e}")

    return respostas
