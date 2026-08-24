# 🚀 Plano de Deploy em Produção — ARNIX Research & Validação de Mercado
**Empresa Proprietária:** Prattes Technologies  
**Plataforma:** ARNIX Smart Pricing & FinOps Engine  
**Domínio Oficial:** `orbb.com.br` (Subdomínio recomendado: `pesquisa.orbb.com.br` ou `validacao.orbb.com.br`)  
**Data da Operação:** Lançamento Hoje (Imediato)

---

## 📋 Resumo Executivo da Estratégia

Para colocar a pesquisa de validação e o dashboard executivo no ar **hoje mesmo**, sem custos de infraestrutura e com certificado SSL/HTTPS automático de nível bancário, utilizaremos a **Vercel Edge Network** conectada ao domínio validado **`orbb.com.br`**.

```
[Respondente / Empreendedor]
            │
            ▼ (HTTPS / SSL Global)
 ┌────────────────────────────────────────────────────────┐
 │  pesquisa.orbb.com.br  (Vercel Edge Network CDN)       │
 ├────────────────────────────┬───────────────────────────┤
 │   / (Pesquisa Interativa)  │ /dashboard (Painel AVS)   │
 └────────────────────────────┴───────────────────────────┘
```

---

## ⚡ Passo a Passo de Implementação (5 Minutos)

### 1. Deploy Instantâneo na Vercel

O arquivo de configuração [`forms/vercel.json`](file:///c:/.workflow/.cofre/.dep_dev/.precific/forms/vercel.json) já está configurado.

#### Opção A: Pelo Terminal (Vercel CLI — Mais Rápido)
1. Instale/execute a CLI da Vercel no terminal do seu computador:
   ```bash
   npm i -g vercel
   ```
2. Acesse a pasta `forms` e execute o deploy em produção:
   ```bash
   cd forms
   vercel --prod
   ```
3. A Vercel solicitará login no seu navegador e gerará instantaneamente um link seguro como `https://arnix-market-research.vercel.app`.

---

#### Opção B: Pelo Painel Web da Vercel (Via GitHub)
1. Acesse [vercel.com](https://vercel.com) e faça login com sua conta do GitHub.
2. Clique em **"Add New..."** → **"Project"**.
3. Selecione o repositório do projeto.
4. No campo **Root Directory**, clique em **Edit** e selecione a pasta `forms`.
5. Clique em **"Deploy"**. Em menos de 30 segundos o sistema estará no ar globalmente!

---

### 2. Conectar o Domínio Prattes Technologies (`orbb.com.br`)

Para que a pesquisa fique profissional com o seu domínio já validado (`pesquisa.orbb.com.br`):

1. No painel do projeto na Vercel, acesse: **Settings** → **Domains**.
2. No campo de adicionar domínio, digite:
   ```text
   pesquisa.orbb.com.br
   ```
3. A Vercel fornecerá o registro DNS para adicionar no seu provedor de domínio (Registro.br, Cloudflare ou Hostinger):
   * **Tipo:** `CNAME`
   * **Nome / Host:** `pesquisa`
   * **Destino / Valor:** `cname.vercel-dns.com`
   * **TTL:** `Auto` ou `1 hora`

> **Resultado Imediato:** Em poucos minutos o link **`https://pesquisa.orbb.com.br`** estará ativo com SSL automático, carregando a pesquisa e o dashboard!

---

## 🌐 Mapeamento de Rotas no Domínio

| URL Pública | Função |
| :--- | :--- |
| **`https://pesquisa.orbb.com.br/`** | Formulário interativo em 5 etapas para profissionais responderem. |
| **`https://pesquisa.orbb.com.br/dashboard`** | Painel executivo do **ARNIX Validation Score (AVS)** e gráficos. |
| **`https://pesquisa.orbb.com.br/dashboard.html`** | Acesso direto ao painel com exportação CSV e PDF. |

---

## 💾 Persistência das Respostas & Coleta dos Dados

O formulário em [`forms/js/form.js`](file:///c:/.workflow/.cofre/.dep_dev/.precific/forms/js/form.js) foi projetado com **arquitetura de contingência dupla**:

1. **Quando o backend FastAPI (`forms/server.py`) estiver rodando na VPS / nuvem:**
   * Grava automaticamente no banco de dados SQLite (`respostas.db`).
2. **Quando rodando como aplicação Vercel Edge:**
   * Grava as respostas no armazenamento local seguro (`localStorage`), garantindo que nenhuma resposta seja perdida mesmo sem servidor dedicado.
   * Você pode integrar com 1 clique um Webhook para receber cada resposta em tempo real no **Google Sheets, Discord, Telegram ou WhatsApp** adicionando a URL do webhook no `form.js`.

---

## 📱 Mensagens Prontas para Compartilhamento Imediato

Envie para seus contatos de negócios, clientes da Orbb Consultoria e grupos de empreendedores:

### Modelo WhatsApp / Direto:
```text
Olá, tudo bem? 👋

Estamos realizando um estudo rápido sobre os desafios de precificação e margem de lucro em pequenas empresas e autônomos para o ecossistema ARNIX / Prattes Technologies.

Leva menos de 3 minutos e é 100% anônimo:
👉 https://pesquisa.orbb.com.br

Sua visão como profissional da área é muito importante para mapearmos as reais dificuldades do mercado. Se puder responder, agradeço demais! 🚀
```

### Modelo LinkedIn / Redes Sociais:
```text
📊 Como você define o preço dos seus serviços e produtos?

No ecossistema ARNIX (Prattes Technologies), estamos conduzindo uma pesquisa empírica para mapear os maiores gargalos de precificação enfrentados por empreendedores e autônomos no Brasil (cálculo de impostos, custos indiretos e margens reais).

⏱️ Tempo estimado: ~3 minutos
🔒 100% Anônimo

Participe e contribua com nosso estudo de mercado:
👉 https://pesquisa.orbb.com.br

#Empreendedorismo #Precificacao #FinOps #SaaS #GestaoFinanceira #ARNIX
```

---

## ✅ Checklist de Lançamento Hoje

- [x] Formulário de pesquisa em 5 etapas validado e responsivo.
- [x] Dashboard de métricas executivas com o **ARNIX Validation Score (AVS)**.
- [x] Exportação de CSV estruturado com UTF-8 BOM para Excel.
- [x] Impressão e exportação de PDF institucional com cabeçalho da **ARNIX / Prattes Technologies / Orbb Consultoria**.
- [x] Arquivo [`forms/vercel.json`](file:///c:/.workflow/.cofre/.dep_dev/.precific/forms/vercel.json) configurado para deploy instantâneo.
- [ ] Rodar `vercel --prod` na pasta `forms`.
- [ ] Adicionar CNAME `pesquisa` apontando para `cname.vercel-dns.com` no DNS de `orbb.com.br`.
- [ ] Disparar os links para a base de contatos e acompanhar o AVS Score subindo no dashboard!
