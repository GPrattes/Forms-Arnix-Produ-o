#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARNIX Research — API Endpoint: /api/health
"""
import os
import sys
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import db as db_module

app = FastAPI(title="ARNIX Health Endpoint")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/api/health")
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "is_postgres": db_module.IS_POSTGRES,
        "is_vercel": db_module.IS_VERCEL,
        "db_url_found": bool(db_module.DB_URL),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

handler = app
