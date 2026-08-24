# 🛠️ Relatório de Engenharia — Desafios Enfrentados e Soluções Arquiteturais
**Projeto:** ARNIX Research & Market Validation Platform  
**Empresa Proprietária:** Prattes Technologies / Orbb Tecnologia & Consultoria  
**Finalidade:** Documentação técnica para portfólio, governança e bancas de avaliação (Empreenda 2026)  
**Classificação:** Documento Público Sanitizado *(Livre de credenciais, chaves ou segredos operacionais)*  

---

## 📌 Sumário Executivo

Durante o ciclo de desenvolvimento, modernização arquitetural e publicação em nuvem do ecossistema **ARNIX**, diversos desafios complexos de infraestrutura Serverless, segurança de dados, propagação de DNS, roteamento de borda e integridade transacional foram solucionados.

Este documento detalha tecnicamente cada obstáculo encontrado e a respectiva solução de engenharia adotada.

---

## 🧱 1. Desafio: Roteamento Híbrido Serverless & Resolução de 404 (Not Found)

### 🔴 O Problema:
Ao migrar a aplicação para a infraestrutura Serverless da Vercel utilizando Python/FastAPI no backend e HTML5/Vanilla CSS no frontend, a função Serverless capturava a rota raiz `/`. Como o framework FastAPI não possuía manipuladores de arquivos estáticos configurados para a raiz, a aplicação retornava um payload JSON `{"detail": "Not Found"}` em vez de renderizar a página do formulário.

### 🟢 A Solução de Engenharia:
1. **Roteamento Dual em `forms/api/index.py`:**  
   Implementação de rotas estáticas explícitas utilizando `FileResponse` do FastAPI para servir com segurança as páginas `/`, `/dashboard`, `/sobre` e `/fundador`.
2. **Montagem de Diretórios Estáticos (`StaticFiles`):**  
   Montagem dos diretórios `/css`, `/js` e `/img` para servir stylesheets, scripts e identidades visuais de forma assíncrona.
3. **Regras de Rewrite Canônicas em `vercel.json`:**  
   Configuração de regras de reescrita limpas (`cleanUrls: true`, `trailingSlash: false`), direcionando chamadas de API para `/api/index.py` e roteando visualizações de página diretamente na borda (Edge Network).

```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/index.py" },
    { "source": "/dashboard", "destination": "/dashboard.html" },
    { "source": "/sobre", "destination": "/sobre.html" },
    { "source": "/fundador", "destination": "/fundador.html" },
    { "source": "/", "destination": "/index.html" }
  ]
}
```

---

## 💾 2. Desafio: Restrição de Sistema de Arquivos Serverless (Read-Only Filesystem)

### 🔴 O Problema:
Em plataformas de computação Serverless (Vercel / AWS Lambda), o diretório do código-fonte é montado como somente leitura. Qualquer tentativa de escrita ou criação de banco de dados SQLite local no diretório da aplicação resultava no erro fatal do sistema operacional: `OSError: [Errno 30] Read-only file system`.

### 🟢 A Solução de Engenharia:
1. **Driver de Banco Dual e Inteligente (`forms/backend/db.py`):**  
   O sistema foi arquitetado para detectar dinamicamente se está rodando em ambiente local ou na nuvem Serverless (`IS_VERCEL`).
2. **Isolamento de Escrita em `/tmp`:**  
   Caso o SQLite seja utilizado em ambiente Serverless, o arquivo do banco é automaticamente redirecionado para `/tmp/arnix_respostas.db` (única partição com permissão de escrita temporária).
3. **Integração Nativa com PostgreSQL na Nuvem (Neon/Vercel Postgres):**  
   Priorização do driver PostgreSQL de alta concorrência com conexão segura via SSL (`sslmode=require`), garantindo persistência duradoura e escalabilidade horizontal.

---

## 🌐 3. Desafio: Roteamento de DNS e Propagação de Subdomínio no Cloudflare

### 🔴 O Problema:
Após a criação do subdomínio `arnix-forms.orbb.com.br`, os navegadores apresentavam falha temporária de resolução (`ERR_NAME_NOT_RESOLVED`), gerada pelo cache DNS negativo (NXDOMAIN) nos resolvedores locais dos provedores de internet (ISPs).

### 🟢 A Solução de Engenharia:
1. **Criação de Registro CNAME Canônico:**  
   Apontamento de `arnix-forms` diretamente para o hostname do cluster Vercel (`cname.vercel-dns.com`).
2. **Diagnóstico e Teste de Autoridade:**  
   Execução de testes de propagação em servidores autoritativos globais (`1.1.1.1` e `8.8.8.8`) e teste de requisição HTTP direta com resolução forçada de IP (`76.76.21.61`), comprovando a emissão correta do certificado SSL/TLS (Let's Encrypt / Vercel Edge).
3. **Flush de Cache Local:**  
   Instruções de renovação de cache de resolução de DNS do cliente (`ipconfig /flushdns`).

---

## 🔒 4. Desafio: Blindagem de Dados Sensíveis e Acesso Exclusivo ao Dashboard

### 🔴 O Problema:
O repositório do projeto é público (portfólio e avaliação acadêmica). No entanto, o sistema coleta dados estratégicos de validação de mercado e potenciais leads comerciais (e-mails e WhatsApp). O painel de métricas e os dados brutos não poderiam ser acessíveis ao público geral.

### 🟢 A Solução de Engenharia:
1. **Proteção no Nível de API (Backend Dependency Guard):**  
   Implementação de um injetor de dependências no FastAPI (`Depends(verify_admin_token)`).
   * A rota `POST /api/respostas` permaneceu **pública e anônima** (Write-Only).
   * As rotas de leitura (`GET /api/respostas`, `GET /api/metricas`, `GET /api/exportar/csv`) foram bloqueadas com **código HTTP 401 Unauthorized** para qualquer requisição sem token administrativo válido.
2. **Gateway de Autenticação no Frontend (`dashboard.html`):**  
   Implementação de um modal escuro de controle de acesso com backdrop blur, exigindo a Chave Mestre de Administrador para desbloquear os gráficos e a renderização das métricas.
3. **Isolamento de Segredos Operacionais:**  
   Todas as senhas, instruções de contingência e manuais de administração foram movidos exclusivamente para a pasta `forms/docs/`, protegida de forma estrita no `.gitignore` e nunca enviada ao repositório público.

---

## 🔄 5. Desafio: Atualização da Suíte de Testes do Pipeline de CI/CD (GitHub Actions)

### 🔴 O Problema:
Após a ativação da trava de segurança no backend, o pipeline automatizado do GitHub Actions falhou no job de testes unitários porque tentava consultar o endpoint `/api/metricas` sem passar credenciais de autenticação, recebendo `401 Unauthorized`.

### 🟢 A Solução de Engenharia:
1. **Refatoração dos Testes de Integração em `.github/workflows/ci-cd.yml`:**  
   O teste automatizado foi aprimorado para validar a própria política de segurança (Security by Design):
   * Testa que chamadas sem token são **corretamente rejeitadas com 401**.
   * Testa que chamadas com o token administrativo são **autorizadas com 200**.
   * Testa que todas as páginas institucionais (`/`, `/dashboard`, `/sobre`, `/fundador`) respondem com **status 200 OK**.

---

## 🚫 6. Desafio: Prevenção de Duplicação e Integridade Estatística da Pesquisa

### 🔴 O Problema:
Respondentes poderiam enviar o formulário repetidas vezes (por cliques duplos em botões ou reenvios propositais), distorcendo o cálculo do **ARNIX Validation Score (AVS)**.

### 🟢 A Solução de Engenharia:
Implementação de um **Mecanismo Anti-Duplicação em 4 Camadas**:
1. **Fingerprint Criptográfico SHA-256:**  
   Geração de hash determinístico combinando as respostas essenciais e o contato (`sha256(client_uuid + lead + segmento + metodo + wtp)`).
2. **Identificador Único de Dispositivo (Client UUID):**  
   Geração e armazenamento persistente de um UUID aleatório no navegador do respondente (`localStorage.getItem('arnix_device_uuid')`).
3. **Verificação de Unicidade por Lead (`lead_contato`):**  
   Se um mesmo e-mail ou telefone for submetido mais de uma vez, o banco de dados detecta o contato existente e rejeita a duplicata (`duplicado_ignorado`).
4. **Migração Automática de Esquema no Banco:**  
   Implementação de rotina de migração em tempo de execução (`init_database`) que verifica e adiciona as colunas `client_uuid` e `fingerprint_hash` nas tabelas SQLite e PostgreSQL existentes sem interrupção de serviço.

---

## 🔌 7. Desafio: Compatibilidade de Variáveis de Ambiente Neon/Vercel (Multi-Prefix)

### 🔴 O Problema:
Diferentes interfaces da Vercel ou integrações com o Neon podem injetar as credenciais de banco sob variáveis de ambiente distintas (`POSTGRES_URL`, `DATABASE_URL`, `ARMAZENAR_URL` ou `NEON_DATABASE_URL`).

### 🟢 A Solução de Engenharia:
Desenvolvimento de um **Resolvedor Universal de Conexão** em `forms/backend/db.py`:
* Checa em cascata as variáveis de ambiente padrão.
* Executa uma varredura dinâmica no dicionário de ambiente (`os.environ`) procurando por qualquer chave com sufixo `_URL` contendo os protocolos `postgres://` ou `postgresql://`.
* Normaliza automaticamente strings legadas `postgres://` para `postgresql://` exigidas pelos drivers Python modernos (`psycopg2`).

---

## 📊 Tabela Resumo dos Desafios e Correções

| Componente | Desafio Original | Causa Raiz | Solução Aplicada | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Roteamento Vercel** | Erro 404 / Not Found na raiz | Rota `/` não capturada no FastAPI | Mapeamento estático e rewrites no `vercel.json` | 🟢 Resolvido |
| **Persistência Serverless** | `OSError: [Errno 30] Read-only` | Tentativa de escrita SQLite no bundle | Fallback `/tmp` e conexão Vercel Postgres (Neon) | 🟢 Resolvido |
| **DNS & Domínio** | `ERR_NAME_NOT_RESOLVED` | Propagação e cache DNS local | CNAME `cname.vercel-dns.com` + flush DNS | 🟢 Resolvido |
| **Segurança & Dados** | Risco de vazamento de leads e métricas | Endpoints públicos sem auth | Backend Dependency Guard (`401`) + Admin Overlay | 🟢 Resolvido |
| **CI/CD GitHub** | Pipeline quebrando no teste | Teste antigo sem header de autenticação | Atualização de asserções de segurança no workflow | 🟢 Resolvido |
| **Integridade de Dados** | Respostas duplicadas poluindo AVS | Múltiplos envios por usuário | Fingerprint SHA-256 + Device UUID + Trava Client | 🟢 Resolvido |
| **Integração Neon** | Múltiplos prefixos de env vars | Variação de idioma/integração Vercel | Resolvedor dinâmico universal de connection string | 🟢 Resolvido |

---

> 🏢 **ARNIX Platform • Prattes Technologies & Orbb Tecnologia & Consultoria**  
> *Engenharia de Software, Governança de Dados e Arquitetura Cloud © 2026*
