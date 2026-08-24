/**
 * ══════════════════════════════════════════════════════════════
 * ARNIX RESEARCH FORM — LOGIC & STEP NAVIGATION
 * Features: Step wizard, validation, animated progress bar,
 * offline-first fallback, and submission to backend / localStorage.
 * ══════════════════════════════════════════════════════════════
 */

// Estado das respostas
const surveyData = {
  // Etapa 1
  relacao_negocio: '',
  porte_negocio: '',
  segmento: '',

  // Etapa 2
  metodo_atual: '',
  frequencia_dificuldade: null,
  dificuldades: [],

  // Etapa 3
  perdeu_venda_preco_alto: '',
  teve_prejuizo_preco_baixo: '',
  tempo_gasto: '',
  importancia_melhorar: null,

  // Etapa 4
  resolveria_problema: '',

  // Etapa 5
  utilizaria_ferramenta: '',
  frequencia_uso: '',
  disposicao_pagamento: '',
  lead_contato: '',

  // Metadados & Anti-duplicação
  client_uuid: '',
  criado_em: new Date().toISOString()
};

let currentStepIndex = 0;

document.addEventListener('DOMContentLoaded', () => {
  initDeviceUUID();
  initTheme();
});

/* ── 0. IDENTIFICADOR ÚNICO DE DISPOSITIVO (ANTI-DUPLICAÇÃO) ─ */
function initDeviceUUID() {
  let uuid = localStorage.getItem('arnix_device_uuid');
  if (!uuid) {
    uuid = 'dev_' + Math.random().toString(36).substring(2, 11) + Date.now().toString(36);
    localStorage.setItem('arnix_device_uuid', uuid);
  }
  surveyData.client_uuid = uuid;
}

/* ── 1. NAVEGAÇÃO ENTRE ETAPAS ────────────────────────────── */
function nextStep(stepIndex) {
  // Esconde todas as etapas
  document.querySelectorAll('.step-pane').forEach(pane => {
    pane.classList.remove('active');
  });

  const targetPane = document.getElementById(`step-${stepIndex}`);
  if (targetPane) {
    targetPane.classList.add('active');
    currentStepIndex = stepIndex;

    // Atualiza visibilidade e preenchimento da barra de progresso
    const progressSection = document.getElementById('progressSection');
    if (stepIndex === 0 || stepIndex === 6) {
      progressSection.style.display = 'none';
    } else {
      progressSection.style.display = 'block';
      updateProgressBar(stepIndex);
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

function updateProgressBar(step) {
  // Total de 5 etapas de perguntas
  const percent = Math.min(100, Math.round((step / 5) * 100));
  const fill = document.getElementById('progressBarFill');
  const stepLabel = document.getElementById('progressStepLabel');
  const percentLabel = document.getElementById('progressPercentLabel');

  if (fill) fill.style.width = `${percent}%`;
  if (stepLabel) stepLabel.textContent = `Etapa ${step} de 5`;
  if (percentLabel) percentLabel.textContent = `${percent}% concluído`;
}

/* ── 2. SELEÇÃO DE OPÇÕES (SINGLE / MULTI / RATING) ────────── */
function selectSingleChoice(element, fieldName, value) {
  const container = element.parentElement;
  container.querySelectorAll('.choice-card').forEach(card => card.classList.remove('selected'));
  element.classList.add('selected');
  surveyData[fieldName] = value;
}

function toggleMultiChoice(element, fieldName, value) {
  element.classList.toggle('selected');
  if (!Array.isArray(surveyData[fieldName])) {
    surveyData[fieldName] = [];
  }

  const index = surveyData[fieldName].indexOf(value);
  if (index > -1) {
    surveyData[fieldName].splice(index, 1);
  } else {
    surveyData[fieldName].push(value);
  }
}

function selectRating(fieldName, ratingValue, buttonElement) {
  const container = buttonElement.parentElement;
  container.querySelectorAll('.rating-btn').forEach(btn => btn.classList.remove('selected'));
  buttonElement.classList.add('selected');
  surveyData[fieldName] = ratingValue;
}

/* ── 3. VALIDAÇÃO ANTES DE AVANÇAR ─────────────────────────── */
function validateAndNext(currentStep, nextStepNumber) {
  let isValid = true;
  let errorMsg = '';

  if (currentStep === 1) {
    if (!surveyData.relacao_negocio) {
      isValid = false;
      errorMsg = 'Por favor, selecione sua relação com o negócio.';
    } else if (!surveyData.porte_negocio) {
      isValid = false;
      errorMsg = 'Por favor, selecione o porte aproximado do negócio.';
    } else if (!surveyData.segmento) {
      isValid = false;
      errorMsg = 'Por favor, selecione o segmento de atuação.';
    }
  } else if (currentStep === 2) {
    if (!surveyData.metodo_atual) {
      isValid = false;
      errorMsg = 'Por favor, selecione como você define o preço atualmente.';
    } else if (!surveyData.frequencia_dificuldade) {
      isValid = false;
      errorMsg = 'Por favor, informe na escala de 1 a 5 a frequência da dificuldade.';
    }
  } else if (currentStep === 3) {
    if (!surveyData.perdeu_venda_preco_alto) {
      isValid = false;
      errorMsg = 'Por favor, responda se já deixou de vender por preço alto.';
    } else if (!surveyData.teve_prejuizo_preco_baixo) {
      isValid = false;
      errorMsg = 'Por favor, responda se já teve prejuízo por cobrar abaixo.';
    } else if (!surveyData.tempo_gasto) {
      isValid = false;
      errorMsg = 'Por favor, selecione o tempo gasto para calcular o preço.';
    } else if (!surveyData.importancia_melhorar) {
      isValid = false;
      errorMsg = 'Por favor, avalie de 1 a 5 a importância de melhorar seu processo.';
    }
  } else if (currentStep === 4) {
    if (!surveyData.resolveria_problema) {
      isValid = false;
      errorMsg = 'Por favor, responda se a solução ARNIX resolveria seus problemas.';
    }
  }

  if (!isValid) {
    alert(errorMsg);
    return;
  }

  nextStep(nextStepNumber);
}

/* ── 4. SUBMIT / ENVIO DAS RESPOSTAS ────────────────────────── */
async function submitSurvey() {
  // Validações da última etapa
  if (!surveyData.utilizaria_ferramenta) {
    alert('Por favor, responda se você utilizaria uma ferramenta como o ARNIX.');
    return;
  }
  if (!surveyData.frequencia_uso) {
    alert('Por favor, selecione com que frequência utilizaria.');
    return;
  }
  if (!surveyData.disposicao_pagamento) {
    alert('Por favor, selecione quanto estaria disposto a pagar.');
    return;
  }

  const leadInput = document.getElementById('lead_contato');
  surveyData.lead_contato = leadInput ? leadInput.value.trim() : '';

  const submitBtn = document.getElementById('btnSubmitForm');
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>Salvando respostas...</span>';
  }

  // Gera sempre um ID de resposta único para a submissão
  surveyData.id = 'resp_' + Date.now().toString(36) + '_' + Math.random().toString(36).substring(2, 6);

  try {
    // 1. Tenta enviar para o backend FastAPI (se estiver ativo)
    const response = await fetch('/api/respostas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(surveyData)
    });

    if (!response.ok) {
      throw new Error('Falha no servidor');
    }
    
    // Marca como respondido com sucesso
    localStorage.setItem('arnix_survey_submitted', 'true');
  } catch (err) {
    // 2. Fallback offline no localStorage (garante que NUNCA perde uma resposta!)
    const localStore = JSON.parse(localStorage.getItem('arnix_survey_responses') || '[]');
    localStore.push({
      ...surveyData,
      id: 'resp_' + Date.now().toString(36)
    });
    localStorage.setItem('arnix_survey_responses', JSON.stringify(localStore));
    localStorage.setItem('arnix_survey_submitted', 'true');
  }

  // Se o usuário preencheu o e-mail/WhatsApp, exibe o cartão de confirmação de lembrete
  if (surveyData.lead_contato) {
    const badge = document.getElementById('emailConfirmationBadge');
    const leadText = document.getElementById('displayUserLead');
    if (badge && leadText) {
      leadText.textContent = surveyData.lead_contato;
      badge.style.display = 'block';
    }
  }

  // Avança para tela de sucesso
  nextStep(6);
}

/* ── 5. TEMA (DARK / LIGHT) ────────────────────────────────── */
function initTheme() {
  const root = document.documentElement;
  const toggleBtn = document.getElementById('themeToggle');
  const toggleText = document.getElementById('themeToggleText');

  const savedTheme = localStorage.getItem('arnix_forms_theme') || 'dark';
  applyTheme(savedTheme);

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const nextTheme = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      applyTheme(nextTheme);
    });
  }

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    localStorage.setItem('arnix_forms_theme', theme);
    if (toggleText) {
      toggleText.textContent = theme === 'dark' ? 'Modo Claro' : 'Modo Escuro';
    }
  }
}
