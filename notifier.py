#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
ARNIX Research — Notifier Engine (Zero-Trust Environment-Driven Dispatcher)
===============================================================================
Dispara notificações e alertas de novas respostas de forma 100% segura através
de variáveis de ambiente (sem expor e-mails ou chaves no código público).
"""

import os
import json
import urllib.request
from datetime import datetime, timezone
from typing import Dict, Any

NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "").strip()
WEBHOOK_URL = os.environ.get("WEBHOOK_NOTIFICATION_URL", "").strip()
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "").strip()

def format_notification_body(resp: Dict[str, Any], total_count: int) -> str:
    agora = datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S UTC')
    dores = ", ".join(resp.get("dificuldades", [])) if resp.get("dificuldades") else "Nenhuma dor selecionada"
    lead = resp.get("lead_contato") or "Anônimo (Não informou contato)"
    
    return f"""
======================================================================
🚀 ARNIX RESEARCH — NOVA RESPOSTA RECEBIDA!
======================================================================
📅 Data/Hora: {agora}
📊 Total de Respondentes Validados: {total_count}

👤 PERFIL DO RESPONDENTE:
• Relação / Cargo: {resp.get('relacao_negocio', 'N/A')}
• Porte da Empresa: {resp.get('porte_negocio', 'N/A')}
• Segmento: {resp.get('segmento', 'N/A')}

💡 DIAGNÓSTICO DE PRECIFICAÇÃO:
• Método Atual: {resp.get('metodo_atual', 'N/A')}
• Nível de Dificuldade (1 a 5): {resp.get('frequencia_dificuldade', 'N/A')}/5
• Maiores Dores: {dores}
• Já Perdeu Venda por Preço Alto?: {resp.get('perdeu_venda_preco_alto', 'N/A')}
• Já Teve Prejuízo por Preço Baixo?: {resp.get('teve_prejuizo_preco_baixo', 'N/A')}
• Tempo Médio por Orçamento: {resp.get('tempo_gasto', 'N/A')}

🎯 ADESÃO & VALIDAÇÃO COMERCIAL:
• ARNIX Resolveria o Problema?: {resp.get('resolveria_problema', 'N/A')}
• Utilizaria a Ferramenta?: {resp.get('utilizaria_ferramenta', 'N/A')}
• Frequência de Uso Estimada: {resp.get('frequencia_uso', 'N/A')}
• Disposição a Pagar Mensal (WTP): {resp.get('disposicao_pagamento', 'N/A')}

🎁 CONTATO / LEAD VIP:
• Contato: {lead}
======================================================================
🏢 ARNIX Platform • Prattes Technologies / Orbb Tecnologia & Consultoria
Painel: https://forms-arnix-produ-o.vercel.app/dashboard
"""

def send_notification(resp: Dict[str, Any], total_count: int) -> bool:
    """
    Dispara a notificação de nova resposta se as variáveis de ambiente estiverem ativas.
    Seguro para repositórios públicos: Não executa chamadas se nenhuma variável for configurada.
    """
    # Se nenhuma variável de notificação foi configurada, não faz nada
    if not NOTIFY_EMAIL and not WEBHOOK_URL and not RESEND_API_KEY:
        print(" [INFO] Notificação desativada (configure NOTIFY_EMAIL ou WEBHOOK_NOTIFICATION_URL nas variáveis da Vercel).")
        return False

    body_text = format_notification_body(resp, total_count)
    
    # 1. Tentativa via Resend API (se configurado)
    if RESEND_API_KEY and NOTIFY_EMAIL:
        try:
            url = "https://api.resend.com/emails"
            payload = {
                "from": "ARNIX Research <onboarding@resend.dev>",
                "to": [NOTIFY_EMAIL],
                "subject": f"🚀 [ARNIX] Nova Resposta Recebida! (Total: {total_count} respondentes)",
                "text": body_text
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                    "User-Agent": "ARNIX-Notifier/1.0"
                }
            )
            urllib.request.urlopen(req, timeout=5)
            print(" [OK] Notificação enviada com sucesso via Resend API!")
            return True
        except Exception as e:
            print(f" [!] Erro ao notificar via Resend: {e}")

    # 2. Tentativa via Webhook (Discord / Slack / Telegram / Zapier)
    if WEBHOOK_URL:
        try:
            req = urllib.request.Request(
                WEBHOOK_URL,
                data=json.dumps({
                    "content": f"🚀 **[ARNIX] Nova Resposta de Pesquisa!**\n**Total acumulado:** `{total_count}` respondentes\n**Segmento:** `{resp.get('segmento')}` | **Cargo:** `{resp.get('relacao_negocio')}`\n**Disposição:** `{resp.get('disposicao_pagamento')}`\n**Lead:** `{resp.get('lead_contato') or 'Anônimo'}`"
                }).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "ARNIX-Notifier/1.0"}
            )
            urllib.request.urlopen(req, timeout=5)
            print(" [OK] Notificação enviada via Webhook!")
            return True
        except Exception as e:
            print(f" [!] Erro ao notificar via Webhook: {e}")

    # 3. Tentativa via FormSubmit Cloud Gateway (apenas se NOTIFY_EMAIL estiver definido)
    if NOTIFY_EMAIL:
        try:
            url = "https://formsubmit.co/ajax/" + NOTIFY_EMAIL
            payload = {
                "_subject": f"🚀 [ARNIX Research] Nova Resposta Recebida! (Total: {total_count})",
                "Total_Respondentes": total_count,
                "Cargo_Relacao": resp.get("relacao_negocio"),
                "Porte": resp.get("porte_negocio"),
                "Segmento": resp.get("segmento"),
                "Metodo_Atual": resp.get("metodo_atual"),
                "Dificuldade_1a5": resp.get("frequencia_dificuldade"),
                "Dores": ", ".join(resp.get("dificuldades", [])) if resp.get("dificuldades") else "Nenhuma",
                "Resolveria_Problema": resp.get("resolveria_problema"),
                "Disposicao_Pagamento": resp.get("disposicao_pagamento"),
                "Lead_Contato": resp.get("lead_contato") or "Anônimo",
                "_template": "table"
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "Mozilla/5.0 (ARNIX Engine)"}
            )
            urllib.request.urlopen(req, timeout=6)
            print(f" [OK] Notificação enviada com sucesso para {NOTIFY_EMAIL}!")
            return True
        except Exception as e:
            print(f" [!] Log da notificação: {e}")

    return False
