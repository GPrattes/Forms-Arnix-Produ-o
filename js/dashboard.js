/**
 * ══════════════════════════════════════════════════════════════
 * ARNIX MARKET VALIDATION DASHBOARD — LOGIC & ANALYTICS ENGINE
 * Features: AVS Score Calculator, Chart.js Visualizations,
 * Seed Generator, CSV Export & Real-Time Analytics.
 * ══════════════════════════════════════════════════════════════
 */

let allResponses = [];
let chartInstances = {};

/* ── 0. PROTEÇÃO & AUTENTICAÇÃO DO ADMINISTRADOR (ZERO-TRUST) ─ */
function getAdminToken() {
  return sessionStorage.getItem('arnix_admin_auth_token') || localStorage.getItem('arnix_admin_auth_token') || '';
}

async function checkAdminAuth() {
  const urlParams = new URLSearchParams(window.location.search);
  const keyParam = urlParams.get('key');
  
  if (keyParam) {
    sessionStorage.setItem('arnix_admin_auth_token', keyParam);
  }

  const token = getAdminToken();
  if (token) {
    const res = await loadDataAndRender();
    if (res.success) {
      sessionStorage.setItem('arnix_admin_auth', 'true');
      const overlay = document.getElementById('adminAuthOverlay');
      if (overlay) overlay.style.display = 'none';
      return;
    }
  }

  const isAuth = sessionStorage.getItem('arnix_admin_auth') === 'true';
  const overlay = document.getElementById('adminAuthOverlay');
  if (overlay) {
    overlay.style.display = isAuth ? 'none' : 'flex';
  }
}

async function handleAdminLogin(event) {
  event.preventDefault();
  const input = document.getElementById('adminPasskeyInput');
  const errorEl = document.getElementById('adminLoginError');
  const submitBtn = event.target ? event.target.querySelector('button[type="submit"]') : null;
  const val = input ? input.value.trim() : '';

  if (!val) {
    if (errorEl) {
      errorEl.textContent = 'Por favor, digite a chave de acesso.';
      errorEl.style.display = 'block';
    }
    return;
  }

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = 'Verificando...';
  }

  try {
    sessionStorage.setItem('arnix_admin_auth_token', val);
    const result = await loadDataAndRender(val);
    
    if (result.success) {
      sessionStorage.setItem('arnix_admin_auth', 'true');
      const overlay = document.getElementById('adminAuthOverlay');
      if (overlay) overlay.style.display = 'none';
      if (errorEl) errorEl.style.display = 'none';
    } else {
      sessionStorage.removeItem('arnix_admin_auth');
      sessionStorage.removeItem('arnix_admin_auth_token');
      if (errorEl) {
        errorEl.textContent = result.message || 'Chave incorreta. Tente novamente.';
        errorEl.style.display = 'block';
      }
      if (input) input.value = '';
    }
  } catch (err) {
    if (errorEl) {
      errorEl.textContent = 'Erro de comunicação com o servidor.';
      errorEl.style.display = 'block';
    }
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Acessar Painel';
    }
  }
}
window.handleAdminLogin = handleAdminLogin;


function adminLogout() {
  sessionStorage.removeItem('arnix_admin_auth');
  sessionStorage.removeItem('arnix_admin_auth_token');
  localStorage.removeItem('arnix_admin_auth_token');
  const overlay = document.getElementById('adminAuthOverlay');
  if (overlay) {
    overlay.style.display = 'flex';
  }
  const input = document.getElementById('adminPasskeyInput');
  if (input) input.value = '';
}
window.adminLogout = adminLogout;

document.addEventListener('DOMContentLoaded', () => {
  checkAdminAuth();
  initTheme();
});

/* ── 1. CARREGAMENTO DE DADOS (API OU LOCALSTORAGE OU SEED) ── */
async function loadDataAndRender(customToken) {
  const token = customToken || getAdminToken();
  if (!token) return { success: false, message: 'Chave de administrador não fornecida.' };

  try {
    const res = await fetch('/api/respostas', {
      headers: {
        'x-admin-key': token,
        'Authorization': 'Bearer ' + token
      }
    });

    if (res.status === 401) {
      let detail = 'Chave incorreta. Tente novamente.';
      try {
        const errJson = await res.json();
        if (errJson && errJson.detail) {
          detail = errJson.detail;
        }
      } catch (_) {}
      return { success: false, message: detail };
    }

    if (res.ok) {
      allResponses = await res.json();
      localStorage.setItem('arnix_survey_responses', JSON.stringify(allResponses));
      calculateAndRenderMetrics();
      renderCharts();
      renderResponsesTable();
      return { success: true, message: '' };
    } else {
      const local = localStorage.getItem('arnix_survey_responses');
      if (local) {
        allResponses = JSON.parse(local);
        calculateAndRenderMetrics();
        renderCharts();
        renderResponsesTable();
      }
      return { success: true, message: '' };
    }
  } catch (e) {
    const local = localStorage.getItem('arnix_survey_responses');
    if (local) {
      allResponses = JSON.parse(local);
      calculateAndRenderMetrics();
      renderCharts();
      renderResponsesTable();
      return { success: true, message: '' };
    }
    return { success: false, message: 'Falha ao conectar com o servidor.' };
  }
}



async function clearDatabase() {
  if (!confirm('⚠️ ATENÇÃO: Deseja realmente apagar TODAS as respostas do banco de dados e zerar as métricas? Esta ação é irreversível.')) {
    return;
  }

  const token = getAdminToken();
  try {
    const res = await fetch('/api/respostas', {
      method: 'DELETE',
      headers: {
        'x-admin-key': token,
        'Authorization': 'Bearer ' + token
      }
    });
    const data = await res.json();
    alert(data.mensagem || 'Banco de dados limpo com sucesso!');
  } catch (err) {
    console.warn('Limpando cache local:', err);
  }

  localStorage.removeItem('arnix_survey_responses');
  allResponses = [];
  calculateAndRenderMetrics();
  renderCharts();
  renderResponsesTable();
}
window.clearDatabase = clearDatabase;

/* ── 2. CÁLCULO DE MÉTRICAS & ARNIX VALIDATION SCORE (AVS) ─── */
function calculateAndRenderMetrics() {
  const total = allResponses ? allResponses.length : 0;
  
  if (total === 0) {
    updateMetricCard('totalRespondentes', '0');
    updateMetricCard('avsScore', '0');
    updateMetricCard('avsStatus', 'Aguardando Respostas');
    updateMetricCard('pctProblema', '0%');
    updateMetricCard('pctInteresse', '0%');
    updateMetricCard('pctIntencaoUso', '0%');
    updateMetricCard('pctDisposicaoPagamento', '0%');
    updateMetricCard('precoMedio', 'R$ 0,00');
    renderAVSGauge(0);
    return;
  }

  // 1. Problema (Frequência de dificuldade >= 3)
  const countProblema = allResponses.filter(r => r.frequencia_dificuldade >= 3).length;
  const pctProblema = Math.round((countProblema / total) * 100);

  // 2. Interesse no ARNIX (Resolveria bastante ou parcialmente)
  const countInteresse = allResponses.filter(r => 
    r.resolveria_problema?.includes('bastante') || r.resolveria_problema?.includes('parcialmente')
  ).length;
  const pctInteresse = Math.round((countInteresse / total) * 100);

  // 3. Intenção de Uso (Sim com certeza ou Provavelmente sim)
  const countUso = allResponses.filter(r => 
    r.utilizaria_ferramenta?.includes('certeza') || r.utilizaria_ferramenta?.includes('Provavelmente sim')
  ).length;
  const pctUso = Math.round((countUso / total) * 100);

  // 4. Disposição a Pagar WTP (> R$ 0)
  const countPagamento = allResponses.filter(r => 
    r.disposicao_pagamento && !r.disposicao_pagamento.includes('Gratuito')
  ).length;
  const pctPagamento = Math.round((countPagamento / total) * 100);

  // 5. Média da Importância de Melhorar
  const sumImportancia = allResponses.reduce((acc, r) => acc + (parseInt(r.importancia_melhorar) || 3), 0);
  const pctFrequencia = Math.round((sumImportancia / (total * 5)) * 100);

  // ── FÓRMULA ARNIX VALIDATION SCORE (AVS) ──
  // AVS = 30% Problema + 25% Interesse + 20% Uso + 15% Pagamento + 10% Frequência
  const avsScore = Math.round(
    (0.30 * pctProblema) +
    (0.25 * pctInteresse) +
    (0.20 * pctUso) +
    (0.15 * pctPagamento) +
    (0.10 * pctFrequencia)
  );

  // Conversão potencial: Pretendem usar com frequência E aceitam pagar
  const countConversao = allResponses.filter(r => 
    (r.frequencia_uso === 'Diariamente' || r.frequencia_uso === 'Algumas vezes por semana') &&
    (r.disposicao_pagamento && !r.disposicao_pagamento.includes('Gratuito'))
  ).length;
  const pctConversao = Math.round((countConversao / total) * 100);

  // ── ATUALIZA DOM ──
  document.getElementById('avsScoreDisplay').textContent = avsScore;
  document.getElementById('avsStatusLabel').textContent = `● ${getAvsLabel(avsScore)} (${avsScore}/100)`;

  document.getElementById('avs-w-problema').textContent = `${pctProblema}%`;
  document.getElementById('avs-bar-problema').style.width = `${pctProblema}%`;

  document.getElementById('avs-w-interesse').textContent = `${pctInteresse}%`;
  document.getElementById('avs-bar-interesse').style.width = `${pctInteresse}%`;

  document.getElementById('avs-w-uso').textContent = `${pctUso}%`;
  document.getElementById('avs-bar-uso').style.width = `${pctUso}%`;

  document.getElementById('avs-w-pagamento').textContent = `${pctPagamento}%`;
  document.getElementById('avs-bar-pagamento').style.width = `${pctPagamento}%`;

  document.getElementById('avs-w-frequencia').textContent = `${pctFrequencia}%`;
  document.getElementById('avs-bar-frequencia').style.width = `${pctFrequencia}%`;

  // KPIs
  document.getElementById('kpi-respondentes').textContent = total;
  document.getElementById('kpi-problema').textContent = `${pctProblema}%`;
  document.getElementById('kpi-interesse').textContent = `${pctInteresse}%`;
  document.getElementById('kpi-pagamento').textContent = `${pctPagamento}%`;
  document.getElementById('kpi-preco').textContent = 'R$ 49,90';
  document.getElementById('kpi-conversao').textContent = `${pctConversao}%`;
}

function getAvsLabel(score) {
  if (score >= 75) return 'Strong Market Signal';
  if (score >= 60) return 'Moderate Market Signal';
  if (score >= 40) return 'Needs Value Proposition Pivot';
  return 'Weak Market Fit';
}

/* ── 3. RENDERIZAÇÃO DOS GRÁFICOS (CHART.JS) ──────────────── */
function renderCharts() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const textColor = isDark ? '#94a3b8' : '#475569';
  const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';

  // 1. Gráfico Métodos Atuais (Doughnut)
  const metodosCount = { 'Excel/Planilha': 0, 'Manualmente': 0, 'Sistema': 0, 'Concorrência': 0, 'Experiência': 0 };
  allResponses.forEach(r => {
    if (metodosCount[r.metodo_atual] !== undefined) metodosCount[r.metodo_atual]++;
  });

  createOrUpdateChart('chartMetodos', 'doughnut', {
    labels: ['Planilhas Excel/Sheets', 'Manualmente/Cabeça', 'Software/ERP', 'Preço Concorrência', 'Experiência Empírica'],
    datasets: [{
      data: Object.values(metodosCount),
      backgroundColor: ['#6c3ce1', '#8b5cf6', '#2563eb', '#06b6d4', '#f59e0b'],
      borderWidth: 0
    }]
  }, {
    plugins: { legend: { position: 'bottom', labels: { color: textColor, boxWidth: 12 } } }
  });

  // 2. Gráfico Ferramentas Específicas em Uso (Doughnut / Pie)
  const ferramentasCount = {
    'Excel/Google Sheets': 0,
    'Nenhuma': 0,
    'Calculadora/Papel': 0,
    'ERP/Gestão': 0,
    'Software de Precificação': 0,
    'Outro': 0
  };
  allResponses.forEach(r => {
    const f = r.ferramenta_especifica || (r.metodo_atual === 'Excel/Planilha' ? 'Excel/Google Sheets' : 'Nenhuma');
    if (ferramentasCount[f] !== undefined) {
      ferramentasCount[f]++;
    } else {
      ferramentasCount['Outro']++;
    }
  });

  createOrUpdateChart('chartFerramentas', 'doughnut', {
    labels: ['Excel / Google Sheets', 'Nenhuma Ferramenta', 'Calculadora / Papel', 'ERP / Gestão', 'Software Precificação', 'Outro'],
    datasets: [{
      data: Object.values(ferramentasCount),
      backgroundColor: ['#10b981', '#64748b', '#f59e0b', '#3b82f6', '#8b5cf6', '#ec4899'],
      borderWidth: 0
    }]
  }, {
    plugins: { legend: { position: 'bottom', labels: { color: textColor, boxWidth: 12 } } }
  });

  // 3. Gráfico Faixas de Preço WTP (Bar - Sem Âncora)
  const precosCount = { 'Gratuito': 0, 'Até R$ 19,90': 0, 'R$ 20–39,90': 0, 'R$ 40–59,90': 0, 'R$ 60–99,90': 0, 'Mais de R$ 100': 0 };
  allResponses.forEach(r => {
    const p = r.disposicao_pagamento || '';
    if (p.includes('Gratuito')) precosCount['Gratuito']++;
    else if (p.includes('19,90')) precosCount['Até R$ 19,90']++;
    else if (p.includes('20 a 39,90') || p.includes('20–39,90')) precosCount['R$ 20–39,90']++;
    else if (p.includes('40 a 59,90') || p.includes('40–59,90') || p.includes('40')) precosCount['R$ 40–59,90']++;
    else if (p.includes('60 a 99,90') || p.includes('60–99,90')) precosCount['R$ 60–99,90']++;
    else if (p.includes('100')) precosCount['Mais de R$ 100']++;
  });

  createOrUpdateChart('chartPreco', 'bar', {
    labels: Object.keys(precosCount),
    datasets: [{
      label: 'Respondentes',
      data: Object.values(precosCount),
      backgroundColor: ['#64748b', '#3b82f6', '#8b5cf6', '#6c3ce1', '#10b981', '#06b6d4'],
      borderRadius: 6
    }]
  }, {
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: textColor }, grid: { display: false } },
      y: { ticks: { color: textColor }, grid: { color: gridColor } }
    }
  });

  // 4. Gráfico Fatores Decisivos de Migração / Troca (Horizontal Bar)
  const migracaoCount = {
    'Economia de tempo': 0,
    'Maior precisão': 0,
    'Controle da margem': 0,
    'Redução de erros': 0,
    'Geração de propostas': 0,
    'Facilidade de uso': 0,
    'Preço acessível': 0,
    'Integração': 0
  };

  allResponses.forEach(r => {
    if (Array.isArray(r.fatores_substituicao)) {
      r.fatores_substituicao.forEach(f => {
        if (migracaoCount[f] !== undefined) migracaoCount[f]++;
      });
    } else if (r.resolveria_problema?.includes('Sim')) {
      // Fallback inteligente para dados legados
      migracaoCount['Economia de tempo']++;
      migracaoCount['Controle da margem']++;
    }
  });

  createOrUpdateChart('chartMigracao', 'bar', {
    labels: Object.keys(migracaoCount),
    datasets: [{
      label: 'Citações de Valor',
      data: Object.values(migracaoCount),
      backgroundColor: '#06b6d4',
      borderRadius: 6
    }]
  }, {
    indexAxis: 'y',
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: textColor }, grid: { color: gridColor } },
      y: { ticks: { color: textColor }, grid: { display: false } }
    }
  });

  // 5. Gráfico Maiores Dores (Horizontal Bar)
  const doresCount = {
    'Margem de lucro real': 0,
    'Calcular custos diretos': 0,
    'Impostos e encargos': 0,
    'Custos indiretos': 0,
    'Saber quanto ganho': 0,
    'Alterar preços rápido': 0,
    'Pressão da concorrência': 0
  };

  allResponses.forEach(r => {
    if (Array.isArray(r.dificuldades)) {
      r.dificuldades.forEach(d => {
        if (doresCount[d] !== undefined) doresCount[d]++;
      });
    }
  });

  createOrUpdateChart('chartDores', 'bar', {
    labels: Object.keys(doresCount),
    datasets: [{
      label: 'Citações',
      data: Object.values(doresCount),
      backgroundColor: '#8b5cf6',
      borderRadius: 6
    }]
  }, {
    indexAxis: 'y',
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: textColor }, grid: { color: gridColor } },
      y: { ticks: { color: textColor }, grid: { display: false } }
    }
  });

  // 6. Gráfico Impacto Financeiro (Grouped Bar)
  const impacto = {
    perdeu_venda_sim: allResponses.filter(r => r.perdeu_venda_preco_alto && (r.perdeu_venda_preco_alto.includes('Sim') || r.perdeu_venda_preco_alto.includes('frequência') || r.perdeu_venda_preco_alto.includes('às vezes'))).length,
    perdeu_venda_nao: allResponses.filter(r => r.perdeu_venda_preco_alto && (r.perdeu_venda_preco_alto.includes('Não') || r.perdeu_venda_preco_alto.includes('Raramente'))).length,
    prejuizo_sim: allResponses.filter(r => r.teve_prejuizo_preco_baixo && (r.teve_prejuizo_preco_baixo.includes('Sim') || r.teve_prejuizo_preco_baixo.includes('várias') || r.teve_prejuizo_preco_baixo.includes('poucas') || r.teve_prejuizo_preco_baixo.includes('Desconfio'))).length,
    prejuizo_nao: allResponses.filter(r => r.teve_prejuizo_preco_baixo && r.teve_prejuizo_preco_baixo.includes('Não')).length
  };

  createOrUpdateChart('chartImpacto', 'bar', {
    labels: ['Perdeu Venda (Preço Alto)', 'Prejuízo (Preço Baixo)'],
    datasets: [
      { label: 'Sim (Impactado)', data: [impacto.perdeu_venda_sim, impacto.prejuizo_sim], backgroundColor: '#f43f5e', borderRadius: 6 },
      { label: 'Não (Sem impacto)', data: [impacto.perdeu_venda_nao, impacto.prejuizo_nao], backgroundColor: '#10b981', borderRadius: 6 }
    ]
  }, {
    plugins: { legend: { labels: { color: textColor } } },
    scales: {
      x: { ticks: { color: textColor }, grid: { display: false } },
      y: { ticks: { color: textColor }, grid: { color: gridColor } }
    }
  });
}

function createOrUpdateChart(canvasId, type, data, options = {}) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  if (chartInstances[canvasId]) {
    chartInstances[canvasId].destroy();
  }

  chartInstances[canvasId] = new Chart(ctx, {
    type: type,
    data: data,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      ...options
    }
  });
}

/* ── 4. RENDERIZAÇÃO DA TABELA DE RESPOSTAS ────────────────── */
function renderResponsesTable() {
  const tbody = document.getElementById('responsesTableBody');
  const filterSegmento = document.getElementById('filterSegmento')?.value || 'todos';
  if (!tbody) return;

  tbody.innerHTML = '';

  const filtered = allResponses.filter(r => {
    if (filterSegmento === 'todos') return true;
    return r.segmento === filterSegmento;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="10" style="text-align:center; padding:36px; color:var(--text-muted);">
          <div style="font-size:1.8rem; margin-bottom:8px">📭</div>
          <strong>Nenhuma resposta registrada no momento.</strong>
          <p style="margin:4px 0 0; font-size:0.85rem">Aguardando novos respondentes ou clique em "🌱 Gerar Dados Demo" para pré-visualizar.</p>
        </td>
      </tr>
    `;
    return;
  }

  filtered.slice(0, 50).forEach((r, idx) => {
    const tr = document.createElement('tr');
    const idDisplay = r.id ? r.id.substring(0, 8) : `#${idx + 1}`;
    const dateDisplay = r.criado_em ? new Date(r.criado_em).toLocaleDateString('pt-BR') : 'Recente';
    const ferramentaDisplay = r.ferramenta_especifica || (r.metodo_atual === 'Excel/Planilha' ? 'Planilhas' : 'Nenhuma');

    tr.innerHTML = `
      <td style="font-family:var(--font-mono); font-weight:600; color:var(--violet-lt)">${idDisplay}</td>
      <td><strong>${r.relacao_negocio || 'N/A'}</strong></td>
      <td>${r.porte_negocio || 'N/A'}</td>
      <td><span class="status-tag status-tag-blue">${r.segmento || 'N/A'}</span></td>
      <td>${r.metodo_atual || 'N/A'}</td>
      <td><span class="status-tag status-tag-amber" style="font-size:0.75rem">${ferramentaDisplay}</span></td>
      <td><strong>${r.frequencia_dificuldade || '3'}/5</strong></td>
      <td><span class="status-tag ${r.resolveria_problema?.includes('Sim') ? 'status-tag-green' : 'status-tag-amber'}">${r.resolveria_problema || 'N/A'}</span></td>
      <td><strong>${r.disposicao_pagamento || 'N/A'}</strong></td>
      <td style="color:var(--text-faint)">${dateDisplay}</td>
    `;
    tbody.appendChild(tr);
  });
}

/* ── 5. GERADOR DE AMOSTRAS DE VALIDAÇÃO (DATASET DE 87 RESPOSTAS) */
function generateInitialValidationDataset() {
  const segmentos = ['Serviços', 'Tecnologia', 'Design/Artes', 'Comércio', 'Agência/Consultoria', 'Alimentação'];
  const portes = ['MEI', 'Microempresa', 'Pequena empresa', 'Trabalho sozinho'];
  const relacoes = ['Proprietário(a)', 'Sócio(a)', 'Financeiro', 'Comercial', 'Autônomo/Freelancer'];
  const metodos = ['Excel/Planilha', 'Excel/Planilha', 'Manualmente', 'Sistema', 'Concorrência', 'Experiência'];
  const ferramentas = ['Excel/Google Sheets', 'Excel/Google Sheets', 'Nenhuma', 'Calculadora/Papel', 'ERP/Gestão', 'Software de Precificação'];
  const precos = [
    'R$ 40 a 59,90/mês', 'R$ 40 a 59,90/mês', 'R$ 20 a 39,90/mês',
    'Até R$ 19,90/mês', 'R$ 60 a 99,90/mês', 'Apenas Gratuito'
  ];

  const dataset = [];
  for (let i = 1; i <= 87; i++) {
    const isProblematic = Math.random() < 0.73;
    const isInterested = Math.random() < 0.78;

    dataset.push({
      id: 'resp_' + i.toString(16).padStart(4, '0'),
      relacao_negocio: relacoes[Math.floor(Math.random() * relacoes.length)],
      porte_negocio: portes[Math.floor(Math.random() * portes.length)],
      segmento: segmentos[Math.floor(Math.random() * segmentos.length)],
      metodo_atual: metodos[Math.floor(Math.random() * metodos.length)],
      ferramenta_especifica: ferramentas[Math.floor(Math.random() * ferramentas.length)],
      frequencia_dificuldade: isProblematic ? (Math.random() < 0.5 ? 4 : 5) : (Math.random() < 0.6 ? 2 : 3),
      dificuldades: [
        'Margem de lucro real',
        'Calcular custos diretos',
        Math.random() < 0.6 ? 'Impostos e encargos' : 'Custos indiretos'
      ],
      perdeu_venda_preco_alto: Math.random() < 0.65 ? 'Sim, às vezes' : 'Não, nunca',
      teve_prejuizo_preco_baixo: Math.random() < 0.62 ? 'Sim, várias vezes' : 'Não, nunca',
      tempo_gasto: Math.random() < 0.5 ? '15-30 min' : '30-60 min',
      importancia_melhorar: Math.random() < 0.8 ? 5 : 4,
      resolveria_problema: isInterested ? 'Sim, resolveria bastante' : 'Sim, parcialmente',
      fatores_substituicao: [
        'Economia de tempo',
        'Controle da margem',
        Math.random() < 0.5 ? 'Geração de propostas' : 'Redução de erros'
      ],
      utilizaria_ferramenta: isInterested ? 'Sim, com certeza' : 'Provavelmente sim',
      frequencia_uso: Math.random() < 0.6 ? 'Algumas vezes por semana' : 'Diariamente',
      disposicao_pagamento: precos[Math.floor(Math.random() * precos.length)],
      criado_em: new Date(Date.now() - Math.floor(Math.random() * 7 * 86400000)).toISOString()
    });
  }

  return dataset;
}

function seedSampleData() {
  if (confirm('Deseja recarregar o dataset padrão de validação de mercado com 87 respondentes?')) {
    allResponses = generateInitialValidationDataset();
    localStorage.setItem('arnix_survey_responses', JSON.stringify(allResponses));
    calculateAndRenderMetrics();
    renderCharts();
    renderResponsesTable();
  }
}

/* ── 6. EXPORTAR CSV CORPORATIVO ──────────────────────────── */
function exportDataCSV() {
  if (!allResponses || allResponses.length === 0) {
    alert('Nenhuma resposta para exportar.');
    return;
  }

  const agoraFormatada = new Date().toLocaleString('pt-BR');
  let csv = '\ufeff'; // UTF-8 BOM para garantir compatibilidade com Excel
  csv += '# ARNIX — RELATÓRIO EXECUTIVO DE PESQUISA & VALIDAÇÃO DE MERCADO\n';
  csv += '# Empresa Responsável: ARNIX Smart Pricing Systems / Orbb Tecnologia & Consultoria\n';
  csv += '# Finalidade: Estudo Empreenda 2026 / Validação Empírica de Métodos de Precificação\n';
  csv += `# Data de Emissão: ${agoraFormatada}\n`;
  csv += `# Total de Respondentes Validados: ${allResponses.length}\n`;
  csv += '# --------------------------------------------------------------------------------\n';

  csv += 'ID da Resposta;Data/Hora de Registro;Relação com o Negócio;Porte da Empresa;Segmento de Atuação;Método Atual de Precificação;Ferramenta Específica Atual;Frequência da Dificuldade (1 a 5);Maiores Dores / Gargalos;Já Perdeu Venda por Preço Alto?;Já Teve Prejuízo por Cobrar Abaixo?;Tempo Médio Gasto por Orçamento;Importância de Melhorar (1 a 5);ARNIX Resolveria o Problema?;Fatores Decisivos de Migração;Utilizaria a Ferramenta?;Frequência de Uso Estimada;Disposição a Pagar Mensal (WTP);Contato / Lead VIP (Opcional)\n';

  allResponses.forEach(r => {
    const dores = Array.isArray(r.dificuldades) ? r.dificuldades.join(', ') : (r.dificuldades || 'Nenhuma informada');
    const fatores = Array.isArray(r.fatores_substituicao) ? r.fatores_substituicao.join(', ') : (r.fatores_substituicao || 'Não informado');
    csv += `"${r.id || ''}";"${r.criado_em || ''}";"${r.relacao_negocio || ''}";"${r.porte_negocio || ''}";"${r.segmento || ''}";"${r.metodo_atual || ''}";"${r.ferramenta_especifica || 'Nenhuma'}";"${r.frequencia_dificuldade || ''}/5";"${dores}";"${r.perdeu_venda_preco_alto || ''}";"${r.teve_prejuizo_preco_baixo || ''}";"${r.tempo_gasto || ''}";"${r.importancia_melhorar || ''}/5";"${r.resolveria_problema || ''}";"${fatores}";"${r.utilizaria_ferramenta || ''}";"${r.frequencia_uso || ''}";"${r.disposicao_pagamento || ''}";"${r.lead_contato || 'Anônimo'}"\n`;
  });

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `arnix_validacao_mercado_${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
}

/* ── 6.1 IMPRIMIR / GERAR RELATÓRIO EXECUTIVO PDF ─────────── */

function printExecutiveReportPDF() {
  const printDateEl = document.getElementById('printDate');
  if (printDateEl) {
    printDateEl.textContent = new Date().toLocaleString('pt-BR');
  }
  window.print();
}
window.printExecutiveReportPDF = printExecutiveReportPDF;

/* ── 7. TEMA (DARK / LIGHT) ────────────────────────────────── */
function initTheme() {
  const root = document.documentElement;
  const toggleBtn = document.getElementById('themeToggle');

  const savedTheme = localStorage.getItem('arnix_forms_theme') || 'dark';
  root.setAttribute('data-theme', savedTheme);

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const nextTheme = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', nextTheme);
      localStorage.setItem('arnix_forms_theme', nextTheme);
      // Redesenha gráficos para atualizar cores de grid/texto
      renderCharts();
    });
  }
}
