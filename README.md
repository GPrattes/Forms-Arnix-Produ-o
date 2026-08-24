# 🚀 ARNIX — Sistema de Pesquisa & Validação de Mercado (Market Validation Engine)

Este diretório contém o **mini sistema web de pesquisa empírica e validação de mercado** desenvolvido para o **ARNIX**. Muito superior a um simples formulário estático do Google Forms, o sistema coleta respostas anônimas, calcula indicadores em tempo real e consolida um **painel executivo de evidências de mercado** com a métrica proprietária **ARNIX Validation Score (AVS)**.

---

## 📁 Estrutura de Arquivos

```
forms/
├── index.html          # Formulário de Pesquisa Interativo (Passo a Passo com Progress Bar)
├── dashboard.html      # Painel Executivo (AVS Score, 6 KPIs, 4 Gráficos e Tabela)
├── server.py           # Backend FastAPI autônomo (Porta 8090 / SQLite / Métricas / CSV)
├── css/
│   ├── form.css        # Estilos da Pesquisa (Dark/Light, Cards de Seleção, Escalas)
│   └── dashboard.css   # Estilos do Dashboard (Glassmorphism, AVS Gauge, Gráficos)
├── js/
│   ├── form.js         # Lógica do Formulário (Validação de etapas, envio e offline fallback)
│   └── dashboard.js    # Lógica Analítica (Chart.js, fórmula AVS, gerador de seed e exportação)
└── data/
    └── respostas.db    # Banco de Dados SQLite local com as respostas anonimizadas
```

---

## 🎯 As 5 Etapas Estratégicas da Pesquisa

1. **Apresentação & Anonimato**: Contextualização do objetivo da pesquisa (~3 minutos de duração, sem coleta de CPF/dados pessoais).
2. **Perfil do Respondente**: Segmentação por relação com o negócio (Proprietário, Sócio, Financeiro, Autônomo), porte (MEI, Microempresa, Pequena empresa) e segmento de atuação.
3. **Diagnóstico do Problema & Dores**: Método atual de precificação (Planilhas, Manual, Sistemas, Concorrência), frequência da dificuldade (1 a 5) e maiores gargalos.
4. **Impacto Financeiro & Operacional**: Evidências de perda de vendas por preço alto, histórico de prejuízos por cobrar abaixo e tempo gasto por proposta.
5. **Apresentação do ARNIX & Validação Comercial**: O "pulo do gato" — apresentação do ARNIX como solução, intenção de uso frequente e **disposição a pagar (WTP)** por faixas de preço (R$ 0 a R$ 100+/mês).

---

## 📊 ARNIX Validation Score (AVS)

O sistema calcula automaticamente o **AVS (0 a 100)** através de uma fórmula ponderada:

$$\text{AVS} = (30\% \times \text{Problema}) + (25\% \times \text{Interesse}) + (20\% \times \text{Uso Frequente}) + (15\% \times \text{Disposição a Pagar}) + (10\% \times \text{Frequência da Dor})$$

* **AVS &ge; 75**: *Strong Market Signal* (Forte tração de mercado validada)
* **60 &le; AVS < 75**: *Moderate Market Signal* (Boa aceitação)
* **AVS < 60**: *Needs Pivot* (Requer ajustes no modelo de valor)

---

## 🚀 Como Executar

### Opção 1: Executando o Servidor FastAPI (Recomendado)
```bash
python forms/server.py
```
* **Formulário de Pesquisa:** [http://localhost:8090](http://localhost:8090)
* **Dashboard Executivo:** [http://localhost:8090/dashboard](http://localhost:8090/dashboard)
* **Swagger API Docs:** [http://localhost:8090/docs](http://localhost:8090/docs)

### Opção 2: Visualização Direta (Sem Servidor)
Você também pode abrir os arquivos `forms/index.html` e `forms/dashboard.html` diretamente em qualquer navegador. O sistema possui **mecanismo de contingência offline no `localStorage`** e gerador de dados de demonstração (*Seed Data*) integrado!
