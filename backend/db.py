#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
ARNIX Research — Database Engine (Vercel Postgres & SQLite Anti-Duplication Driver)
===============================================================================
Gerencia a persistência de respostas com proteção total contra duplicação:
1. Deduplicação por Fingerprint Criptográfico (SHA-256)
2. Deduplicação por Identificador de Dispositivo (Client UUID)
3. Deduplicação por Contato/E-mail (Lead Contato)
4. Suporte a Vercel Postgres e SQLite (/tmp no ambiente Serverless)
"""

import os
import sys
import json
import sqlite3
import hashlib
from typing import List, Dict, Any, Optional

# Detecção flexível e universal da URL de conexão PostgreSQL da Vercel/Neon
DB_URL = (
    os.environ.get("POSTGRES_URL") or
    os.environ.get("DATABASE_URL") or
    os.environ.get("POSTGRES_URL_NON_POOLING") or
    os.environ.get("POSTGRES_PRISMA_URL") or
    os.environ.get("ARMAZENAR_URL") or
    os.environ.get("NEON_DATABASE_URL") or
    ""
)

# Varredura dinâmica para qualquer prefixo customizado gerado pela Vercel
if not DB_URL:
    for k, v in os.environ.items():
        if k.endswith("_URL") and isinstance(v, str) and ("postgres" in v or "postgresql" in v):
            DB_URL = v
            break

# Normaliza postgres:// para postgresql:// para compatibilidade com psycopg2
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

IS_POSTGRES = bool(DB_URL and ("postgresql" in DB_URL or "postgres" in DB_URL))
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

def calculate_fingerprint(resp: Dict[str, Any]) -> str:
    """Gera um hash único baseado no dispositivo, contato e respostas principais."""
    client_uuid = (resp.get("client_uuid") or "").strip()
    lead_contato = (resp.get("lead_contato") or "").lower().strip()
    segmento = (resp.get("segmento") or "").strip()
    metodo_atual = (resp.get("metodo_atual") or "").strip()
    freq_dif = str(resp.get("frequencia_dificuldade") or 3)
    wtp = (resp.get("disposicao_pagamento") or "").strip()

    fingerprint_seed = f"{client_uuid}|{lead_contato}|{segmento}|{metodo_atual}|{freq_dif}|{wtp}"
    return hashlib.sha256(fingerprint_seed.encode("utf-8")).hexdigest()[:32]

def init_database():
    """Cria e atualiza a tabela de respostas com índices e proteção anti-duplicação."""
    if IS_POSTGRES:
        try:
            conn = get_postgres_connection()
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS respostas_pesquisa (
                id VARCHAR(64) PRIMARY KEY,
                client_uuid VARCHAR(64),
                fingerprint_hash VARCHAR(64),
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
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='respostas_pesquisa' AND column_name='client_uuid') THEN
                    ALTER TABLE respostas_pesquisa ADD COLUMN client_uuid VARCHAR(64);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='respostas_pesquisa' AND column_name='fingerprint_hash') THEN
                    ALTER TABLE respostas_pesquisa ADD COLUMN fingerprint_hash VARCHAR(64);
                END IF;
            END $$;
            CREATE INDEX IF NOT EXISTS idx_fingerprint ON respostas_pesquisa(fingerprint_hash);
            CREATE INDEX IF NOT EXISTS idx_lead ON respostas_pesquisa(lead_contato);
            """)
            conn.commit()
            cursor.close()
            conn.close()
            print(" [OK] Tabela Vercel Postgres e índices anti-duplicação ativos!")
        except Exception as e:
            print(f" [!] Aviso ao inicializar Vercel Postgres: {e}")
    else:
        try:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS respostas_pesquisa (
                id TEXT PRIMARY KEY,
                client_uuid TEXT,
                fingerprint_hash TEXT,
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
            # Migrações seguras SQLite
            cursor.execute("PRAGMA table_info(respostas_pesquisa);")
            cols = [col[1] for col in cursor.fetchall()]
            if "client_uuid" not in cols:
                cursor.execute("ALTER TABLE respostas_pesquisa ADD COLUMN client_uuid TEXT;")
            if "fingerprint_hash" not in cols:
                cursor.execute("ALTER TABLE respostas_pesquisa ADD COLUMN fingerprint_hash TEXT;")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sqlite_fp ON respostas_pesquisa(fingerprint_hash);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sqlite_lead ON respostas_pesquisa(lead_contato);")
            conn.commit()
            conn.close()
            print(f" [OK] Banco de Dados SQLite verificado com anti-duplicação em {SQLITE_DB_PATH}")
        except Exception as e:
            print(f" [!] Aviso ao inicializar SQLite: {e}")

try:
    init_database()
except Exception as e:
    print(f" [!] Aviso silencioso na inicialização do banco: {e}")

def insert_resposta(resp: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insere uma resposta garantindo que não ocorra duplicação.
    Retorna o status, ID e se foi uma inserção nova ou detecção de duplicado.
    """
    resp_id = resp.get("id")
    client_uuid = resp.get("client_uuid") or ""
    lead_contato = (resp.get("lead_contato") or "").strip()
    fingerprint = calculate_fingerprint(resp)
    dificuldades_json = json.dumps(resp.get("dificuldades", []), ensure_ascii=False)

    # 1. VERIFICAÇÃO NO POSTGRESQL (VERCEL)
    if IS_POSTGRES:
        try:
            conn = get_postgres_connection()
            cursor = conn.cursor()

            # Checa se já existe resposta com o mesmo fingerprint OU com o mesmo lead_contato válido
            if lead_contato:
                cursor.execute(
                    "SELECT id FROM respostas_pesquisa WHERE fingerprint_hash = %s OR (lead_contato = %s AND lead_contato != '') LIMIT 1;",
                    (fingerprint, lead_contato)
                )
            else:
                cursor.execute(
                    "SELECT id FROM respostas_pesquisa WHERE fingerprint_hash = %s OR (client_uuid = %s AND client_uuid != '') LIMIT 1;",
                    (fingerprint, client_uuid)
                )

            existing = cursor.fetchone()
            if existing:
                cursor.close()
                conn.close()
                return {"id": existing["id"], "duplicado": True, "status": "duplicado_ignorado"}

            cursor.execute("""
            INSERT INTO respostas_pesquisa (
                id, client_uuid, fingerprint_hash, relacao_negocio, porte_negocio, segmento, metodo_atual,
                frequencia_dificuldade, dificuldades, perdeu_venda_preco_alto,
                teve_prejuizo_preco_baixo, tempo_gasto, importancia_melhorar,
                resolveria_problema, utilizaria_ferramenta, frequencia_uso,
                disposicao_pagamento, lead_contato, criado_em
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                resp_id, client_uuid, fingerprint, resp.get("relacao_negocio"), resp.get("porte_negocio"), resp.get("segmento"),
                resp.get("metodo_atual"), resp.get("frequencia_dificuldade"), dificuldades_json,
                resp.get("perdeu_venda_preco_alto"), resp.get("teve_prejuizo_preco_baixo"),
                resp.get("tempo_gasto"), resp.get("importancia_melhorar"), resp.get("resolveria_problema"),
                resp.get("utilizaria_ferramenta"), resp.get("frequencia_uso"),
                resp.get("disposicao_pagamento"), lead_contato, resp.get("criado_em")
            ))
            conn.commit()
            cursor.close()
            conn.close()
            return {"id": resp_id, "duplicado": False, "status": "inserido"}
        except Exception as e:
            print(f" [!] Erro ao gravar no Postgres: {e}")

    # 2. VERIFICAÇÃO NO SQLITE
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        if lead_contato:
            cursor.execute(
                "SELECT id FROM respostas_pesquisa WHERE fingerprint_hash = ? OR (lead_contato = ? AND lead_contato != '') LIMIT 1;",
                (fingerprint, lead_contato)
            )
        else:
            cursor.execute(
                "SELECT id FROM respostas_pesquisa WHERE fingerprint_hash = ? OR (client_uuid = ? AND client_uuid != '') LIMIT 1;",
                (fingerprint, client_uuid)
            )

        existing = cursor.fetchone()
        if existing:
            conn.close()
            return {"id": existing[0], "duplicado": True, "status": "duplicado_ignorado"}

        cursor.execute("""
        INSERT INTO respostas_pesquisa (
            id, client_uuid, fingerprint_hash, relacao_negocio, porte_negocio, segmento, metodo_atual,
            frequencia_dificuldade, dificuldades, perdeu_venda_preco_alto,
            teve_prejuizo_preco_baixo, tempo_gasto, importancia_melhorar,
            resolveria_problema, utilizaria_ferramenta, frequencia_uso,
            disposicao_pagamento, lead_contato, criado_em
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            resp_id, client_uuid, fingerprint, resp.get("relacao_negocio"), resp.get("porte_negocio"), resp.get("segmento"),
            resp.get("metodo_atual"), resp.get("frequencia_dificuldade"), dificuldades_json,
            resp.get("perdeu_venda_preco_alto"), resp.get("teve_prejuizo_preco_baixo"),
            resp.get("tempo_gasto"), resp.get("importancia_melhorar"), resp.get("resolveria_problema"),
            resp.get("utilizaria_ferramenta"), resp.get("frequencia_uso"),
            resp.get("disposicao_pagamento"), lead_contato, resp.get("criado_em")
        ))
        conn.commit()
        conn.close()
        return {"id": resp_id, "duplicado": False, "status": "inserido"}
    except Exception as e:
        print(f" [!] Erro ao gravar no SQLite: {e}")

    return {"id": resp_id, "duplicado": False, "status": "fallback"}

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
                    "client_uuid": r.get("client_uuid") or "",
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
                    "lead_contato": r["lead_contato"] or "",
                    "criado_em": r["criado_em"] or ""
                })
            return respostas
        except Exception as e:
            print(f" [!] Erro ao listar do Postgres: {e}")

    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM respostas_pesquisa ORDER BY criado_em DESC;")
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
                "client_uuid": r["client_uuid"] if "client_uuid" in r.keys() else "",
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
                "lead_contato": r["lead_contato"] or "",
                "criado_em": r["criado_em"] or ""
            })
    except Exception as e:
        print(f" [!] Erro ao listar do SQLite: {e}")

    return respostas
