#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
ARNIX Research — High-Reliability Multi-Channel Notifier Engine
===============================================================================
Envia alertas instantâneos de novas respostas de pesquisa para o e-mail do
fundador (gprattesceo@orbb.com.br) e/ou Webhook com cabeçalhos autorizados.
"""

import os
import json
import smtplib
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import Dict, Any

NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "gprattesceo@orbb.com.br").strip()
WEBHOOK_URL = os.environ.get("WEBHOOK_NOTIFICATION_URL", "").strip()
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "").strip()
WEB3FORMS_KEY = os.environ.get("WEB3FORMS_KEY", "").strip()

# Configurações SMTP (opcional via env para envio 100% direto)
SMTP_HOST = os.environ.get("SMTP_HOST", "").strip()
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "").strip()
SMTP_PASS = os.environ.get("SMTP_PASS", "").strip()
SMTP_FROM = os.environ.get("SMTP_FROM", NOTIFY_EMAIL).strip()

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
    """Dispara a notificação através de múltiplos canais redundantes."""
    body_text = format_notification_body(resp, total_count)
    sent_successfully = False

    # 1. Canal 1: SMTP Direto (se configurado)
    if SMTP_HOST and SMTP_USER and SMTP_PASS:
        try:
            msg = MIMEMultipart()
            msg["From"] = SMTP_FROM or SMTP_USER
            msg["To"] = NOTIFY_EMAIL
            msg["Subject"] = f"🚀 [ARNIX] Nova Resposta Recebida! (Total: {total_count})"
            msg.attach(MIMEText(body_text, "plain", "utf-8"))
            
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=8) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(msg["From"], [NOTIFY_EMAIL], msg.as_string())
            print(" [OK] Notificação enviada via SMTP Direto!")
            sent_successfully = True
        except Exception as e:
            print(f" [!] Aviso SMTP: {e}")

    # 2. Canal 2: Resend API (se token fornecido)
    if RESEND_API_KEY and NOTIFY_EMAIL:
        try:
            url = "https://api.resend.com/emails"
            payload = {
                "from": "ARNIX Research <onboarding@resend.dev>",
                "to": [NOTIFY_EMAIL],
                "subject": f"🚀 [ARNIX] Nova Resposta Recebida! (Total: {total_count})",
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
            with urllib.request.urlopen(req, timeout=5) as res:
                if res.status in (200, 201):
                    print(" [OK] Notificação enviada via Resend API!")
                    sent_successfully = True
        except Exception as e:
            print(f" [!] Aviso Resend: {e}")

    # 3. Canal 3: Webhook (Discord / Slack / Telegram / Zapier)
    if WEBHOOK_URL:
        try:
            req = urllib.request.Request(
                WEBHOOK_URL,
                data=json.dumps({
                    "content": f"🚀 **[ARNIX Research] Nova Resposta Recebida!**\n📊 **Total Acumulado:** `{total_count}` respondentes\n🏢 **Segmento:** `{resp.get('segmento')}` | **Cargo:** `{resp.get('relacao_negocio')}`\n💰 **Disposição a Pagar:** `{resp.get('disposicao_pagamento')}`\n✉️ **Lead VIP:** `{resp.get('lead_contato') or 'Anônimo'}`"
                }).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "ARNIX-Notifier/1.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as res:
                if res.status in (200, 204):
                    print(" [OK] Notificação enviada via Webhook!")
                    sent_successfully = True
        except Exception as e:
            print(f" [!] Aviso Webhook: {e}")

    # 4. Canal 4: FormSubmit Cloud Gateway (Com flags anti-spam e template limpo)
    if NOTIFY_EMAIL:
        try:
            url = f"https://formsubmit.co/ajax/{NOTIFY_EMAIL}"
            payload = {
                "_subject": f"🚀 [ARNIX] Nova Resposta de Pesquisa! (Total: {total_count})",
                "_captcha": "false",
                "_template": "table",
                "Total_Respondentes": total_count,
                "Cargo_Relacao": resp.get("relacao_negocio", "N/A"),
                "Porte_Empresa": resp.get("porte_negocio", "N/A"),
                "Segmento": resp.get("segmento", "N/A"),
                "Metodo_Atual": resp.get("metodo_atual", "N/A"),
                "Dificuldade_1a5": resp.get("frequencia_dificuldade", "N/A"),
                "Maiores_Dores": ", ".join(resp.get("dificuldades", [])) if resp.get("dificuldades") else "Nenhuma",
                "Perdeu_Venda_Preco_Alto": resp.get("perdeu_venda_preco_alto", "N/A"),
                "Teve_Prejuizo_Preco_Baixo": resp.get("teve_prejuizo_preco_baixo", "N/A"),
                "Tempo_Gasto": resp.get("tempo_gasto", "N/A"),
                "Resolveria_Problema": resp.get("resolveria_problema", "N/A"),
                "Utilizaria_Ferramenta": resp.get("utilizaria_ferramenta", "N/A"),
                "Frequencia_Uso": resp.get("frequencia_uso", "N/A"),
                "Disposicao_Pagamento": resp.get("disposicao_pagamento", "N/A"),
                "Lead_Contato": resp.get("lead_contato") or "Anônimo"
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "Origin": "https://forms-arnix-produ-o.vercel.app",
                    "Referer": "https://forms-arnix-produ-o.vercel.app/"
                }
            )
            with urllib.request.urlopen(req, timeout=6) as res:
                res_body = res.read().decode("utf-8")
                print(f" [FormSubmit Log]: {res_body}")
                if '"success":"true"' in res_body or "success" in res_body:
                    sent_successfully = True
        except Exception as e:
            print(f" [!] FormSubmit Log: {e}")

    # 5. Canal 5: Web3Forms (se chave presente)
    if WEB3FORMS_KEY and NOTIFY_EMAIL:
        try:
            url = "https://api.web3forms.com/submit"
            payload = {
                "access_key": WEB3FORMS_KEY,
                "subject": f"🚀 [ARNIX] Nova Resposta! (Total: {total_count})",
                "message": body_text,
                "to_email": NOTIFY_EMAIL
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "Accept": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5) as res:
                if res.status in (200, 201):
                    print(" [OK] Notificação enviada via Web3Forms!")
                    sent_successfully = True
        except Exception as e:
            print(f" [!] Aviso Web3Forms: {e}")

    return sent_successfully
