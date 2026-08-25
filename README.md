# 🚀 ARNIX — Sistema de Pesquisa & Validação de Mercado (Market Validation Engine)

Sistema corporativo de pesquisa empírica, captura de evidências de mercado e análise em tempo real para o ecossistema **ARNIX**. A plataforma coleta respostas qualificadas, calcula indicadores analíticos instantaneamente e consolida um **painel executivo com a métrica proprietária ARNIX Validation Score (AVS)**.

---

## 📁 Estrutura do Projeto

```text
forms/
├── index.html          # Formulário de Pesquisa Interativo (Passo a Passo com Validação Fluida)
├── dashboard.html      # Painel Executivo (AVS Score, Gráficos Chart.js e Tabela em Tempo Real)
├── sobre.html          # Página Institucional (Arquitetura, Comparativo ROI e Motores de Cálculo)
├── fundador.html       # Página Oficial do Fundador (Perfil Executivo e Canais Oficiais)
├── api/                # Endpoints Serverless Nativos (FastAPI / Vercel Python Runtime)
│   ├── respostas.py    # Ingestão com Rate Limit e Deduplicação / Leitura Protegida
│   ├── metricas.py     # Cálculo Dinâmico do AVS Score e Taxas de Mercado
│   ├── debug.py        # Diagnóstico de Integridade e Conexão de Banco de Dados
│   └── health.py       # Monitor de Saúde da Infraestrutura
├── backend/            # Camada de Persistência & Serviços
│   ├── db.py           # Engine de Banco de Dados (PostgreSQL Neon + SQLite Fallback)
│   ├── notifier.py     # Disparador Multi-Canal com Contagem de Respondentes
│   └── server.py       # Servidor de Desenvolvimento Local
├── css/                # Folhas de Estilo (Dark/Light Mode, Glassmorphism, Design System)
└── js/                 # Controladores JavaScript (Validação, Telemetria e Dashboard)
```

---

## 🎯 As 5 Etapas Estratégicas da Pesquisa

1. **Apresentação & Anonimato**: Contextualização do objetivo da pesquisa (~2 minutos de duração, sem coleta intrusiva de dados).
2. **Perfil do Respondente**: Segmentação por cargo/relação com o negócio, porte da empresa e segmento de atuação (incluindo Tecnologia, Serviços, Design/Artes, Comércio, etc.).
3. **Diagnóstico do Problema & Dores**: Método atual de precificação, frequência de dificuldade e maiores gargalos operacionais.
4. **Impacto Financeiro & Operacional**: Histórico de perda de vendas por preço alto, ocorrência de prejuízos por cobrar abaixo do custo e tempo gasto em orçamentos.
5. **Apresentação da Solução & Validação Comercial**: Percepção de valor da plataforma, intenção de uso frequente e **disposição a pagar (WTP)** mensal.

---

## 📊 Métrica Proprietária: ARNIX Validation Score (AVS)

O sistema consolida automaticamente as evidências empíricas através da fórmula ponderada de validação:

$$\text{AVS} = (30\% \times \text{Problema}) + (25\% \times \text{Interesse}) + (20\% \times \text{Uso Frequente}) + (15\% \times \text{WTP}) + (10\% \times \text{Frequência})$$

| Faixa de Score | Classificação de Mercado | Significado Estratégico |
| :--- | :--- | :--- |
| **75 a 100** | 🟢 *Strong Market Signal* | Forte validação empírica e tração comercial comprovada |
| **50 a 74** | 🟡 *Moderate Market Signal* | Aceitação consistente com oportunidades de refinamento |
| **0 a 49** | 🔴 *Low Signal* | Necessidade de calibragem de proposta de valor |

---

## 🛡️ Camadas de Segurança & Governança

* **Proteção Anti-DDoS:** Borda Anycast que absorve ataques volumétricos L3/L4/L7 antes da camada de aplicação.
* **Rate Limiting Ativo (*Sliding Window*):** Limite de requisições por IP na ingestão com bloqueio automático contra robôs.
* **Deduplicação Criptográfica:** Hash determinístico SHA-256 e UUID que impede submissões duplicadas da mesma origem.
* **Autenticação Administrativa Timing-Safe:** Verificação em tempo constante de cabeçalhos de autorização para proteção do dashboard.
* **Consultas Parametrizadas:** 100% de *prepared statements* no banco de dados para prevenção contra SQL Injection.
* **Arquitetura Zero-Trust:** Todas as variáveis de ambiente e credenciais são isoladas no servidor, sem exposição no frontend.

---

## 🚀 Como Executar Localmente

### Opção 1: Servidor de Desenvolvimento FastAPI
```bash
python forms/backend/server.py
```
* **Pesquisa:** `http://localhost:8090/`
* **Dashboard:** `http://localhost:8090/dashboard`
* **Sobre:** `http://localhost:8090/sobre`

### Opção 2: Visualização Direta
Você também pode abrir os arquivos `.html` diretamente no navegador. O sistema conta com mecanismo de contingência e armazenamento local para testes offline.

