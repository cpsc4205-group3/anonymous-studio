// Defensive DOM helpers
function createSafeElementStub(id = '') {
  return {
    id, value: '', checked: false, disabled: false, files: [], dataset: {}, style: {},
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    setAttribute() {}, removeAttribute() {}, addEventListener() {}, removeEventListener() {},
    appendChild() {}, remove() {}, click() {}, focus() {}, closest() { return null; },
    querySelector() { return createSafeElementStub(); }, querySelectorAll() { return []; },
    get textContent() { return ''; }, set textContent(_) {},
    get innerHTML() { return ''; }, set innerHTML(_) {},
  };
}
const __realGetElementById = document.getElementById.bind(document);
document.getElementById = (id) => __realGetElementById(id) || createSafeElementStub(id);
const __realQuerySelector = document.querySelector.bind(document);
document.querySelector = (selector) => __realQuerySelector(selector) || createSafeElementStub(selector);

const byId = (id) => document.getElementById(id);
const valueOf = (id, fallback = '') => { const el = byId(id); return el ? el.value : fallback; };
const routePrefix = window.HYBRID_ROUTE_PREFIX || '';
const form = document.getElementById('hybrid-form');
const textInput = document.getElementById('text-input');
const fileInput = document.getElementById('file-input');
const thresholdInput = document.getElementById('threshold');
const thresholdValue = document.getElementById('threshold-value');
const analyzeBtn = document.getElementById('analyze-btn');
const anonymizeBtn = document.getElementById('anonymize-btn');
const selectAllBtn = document.getElementById('select-all-btn');
const clearAllBtn = document.getElementById('clear-all-btn');
const loadSampleBtn = document.getElementById('load-sample-btn');
const clearBtn = document.getElementById('clear-btn');
const originalPreview = document.getElementById('original-preview');
const resultPreview = document.getElementById('result-preview');
const finalOutput = document.getElementById('final-output');
const outputModeLabel = document.getElementById('output-mode-label');
const kpiTotal = document.getElementById('kpi-total');
const kpiBand = document.getElementById('kpi-band');
const kpiConfidence = document.getElementById('kpi-confidence');
const kpiLow = document.getElementById('kpi-low');
const entityMix = document.getElementById('entity-mix');
const bandMix = document.getElementById('band-mix');
const entityBars = document.getElementById('entity-bars');
const entityTableBody = document.querySelector('#entity-table tbody');
const showRationale = document.getElementById('show-rationale');
const messageSlot = document.getElementById('message-slot');
const downloadTextBtn = document.getElementById('download-text-btn');
const downloadEntitiesBtn = document.getElementById('download-entities-btn');
const saveSessionBtn = document.getElementById('save-session-btn');
const sessionList = document.getElementById('session-list');
const sessionCount = document.getElementById('session-count');
const refreshSessionsBtn = document.getElementById('refresh-sessions-btn');
const pipelineCard = document.getElementById('pipeline-card');
const advancedDrawer = document.getElementById('advanced-drawer');
const toggleAdvancedBtn = document.getElementById('toggle-advanced-btn');
const closeAdvancedBtn = document.getElementById('close-advanced-btn');
const operatorSelect = document.getElementById('operator');
const nerModel = document.getElementById('ner-model');
const spacyStatus = document.getElementById('spacy-status');
const synthProvider = document.getElementById('synth-provider');
const synthNote = document.getElementById('synth-note');
const providerFields = document.querySelectorAll('.provider-field');

const navToggleBtn = document.getElementById('hybrid-nav-toggle');
const hybridShell = document.getElementById('hybrid-shell');
const SIDEBAR_STORAGE_KEY = 'hybridSidebarExpanded';

function applySidebarState(expanded) {
  if (!hybridShell || !navToggleBtn) return;
  hybridShell.classList.toggle('is-expanded', expanded);
  hybridShell.classList.toggle('is-collapsed', !expanded);
  navToggleBtn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
}

function initSidebarState() {
  const saved = window.localStorage.getItem(SIDEBAR_STORAGE_KEY);
  applySidebarState(saved === 'true');
}


let lastResult = null;
let savedSessions = Array.isArray(window.INITIAL_SESSIONS) ? window.INITIAL_SESSIONS : [];

const SAMPLE_TEXT = `Patient: Jane Doe\nDOB: 03/15/1982\nEmail: jane.doe@hospital.org\nPhone: +1-800-555-0199\nDoctor: Dr. Robert Kim\nAddress: 123 Main Street, Columbus, Georgia\nSSN: 987-65-4321`;

function apiUrl(path) {
  return `${routePrefix}${path}`;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function setThresholdLabel() {
  thresholdValue.textContent = Number(thresholdInput.value).toFixed(2);
}

function setCheckboxes(checked) {
  document.querySelectorAll('input[name="entities"]').forEach((box) => {
    box.checked = checked;
  });
}

function showMessage(message, kind = 'info') {
  messageSlot.innerHTML = `<div class="message-banner ${kind}">${escapeHtml(message)}</div>`;
}

function clearMessage() {
  messageSlot.innerHTML = '';
}

function createTag(text) {
  return `<span class="tag">${escapeHtml(text)}</span>`;
}

function renderTags(target, entries, emptyText) {
  if (!entries.length) {
    target.innerHTML = `<span class="empty-inline">${escapeHtml(emptyText)}</span>`;
    return;
  }
  target.innerHTML = entries.map(createTag).join('');
}

function renderSegments(target, segments, paneClass, fallbackText) {
  if (!segments || !segments.length) {
    target.textContent = fallbackText;
    target.classList.add('empty-state-box');
    return;
  }
  const html = segments.map((segment) => {
    if (!segment.entityId) return escapeHtml(segment.text);
    const title = `${segment.label} · ${segment.confidence}% confidence`;
    return `<span class="segment-entity ${paneClass === 'result' ? 'segment-result' : ''}" data-entity-id="${escapeHtml(segment.entityId)}" title="${escapeHtml(title)}">${escapeHtml(segment.text)}</span>`;
  }).join('');
  target.innerHTML = html;
  target.classList.remove('empty-state-box');
}

function attachLinkedHover() {
  document.querySelectorAll('.segment-entity').forEach((element) => {
    element.addEventListener('mouseenter', () => {
      const entityId = element.dataset.entityId;
      document.querySelectorAll(`[data-entity-id="${entityId}"]`).forEach((match) => match.classList.add('is-linked'));
    });
    element.addEventListener('mouseleave', () => {
      const entityId = element.dataset.entityId;
      document.querySelectorAll(`[data-entity-id="${entityId}"]`).forEach((match) => match.classList.remove('is-linked'));
    });
  });
}

function renderEntityBars(counts) {
  const entries = Object.entries(counts || {});
  if (!entries.length) {
    entityBars.innerHTML = '<span class="empty-inline">Run an analysis to populate this chart.</span>';
    return;
  }
  const max = Math.max(...entries.map(([, value]) => value), 1);
  entityBars.innerHTML = entries.map(([name, value]) => {
    const width = Math.max(8, Math.round((value / max) * 100));
    return `
      <div class="bar-row">
        <span>${escapeHtml(name)}</span>
        <div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div>
        <strong>${escapeHtml(value)}</strong>
      </div>`;
  }).join('');
}

function renderEntityTable(rows) {
  const showFull = showRationale.checked;
  document.querySelectorAll('.rationale-col').forEach((node) => {
    node.style.display = showFull ? '' : 'none';
  });

  if (!rows || !rows.length) {
    entityTableBody.innerHTML = `<tr><td colspan="${showFull ? 7 : 5}" class="table-empty">No entities detected for this input.</td></tr>`;
    return;
  }

  entityTableBody.innerHTML = rows.map((row) => `
    <tr>
      <td>${escapeHtml(row.entityType)}</td>
      <td>${escapeHtml(row.text)}</td>
      <td>${escapeHtml(row.confidence)}%</td>
      <td>${escapeHtml(row.confidenceBand)}</td>
      <td>${escapeHtml(`${row.start}-${row.end}`)}</td>
      <td class="rationale-col" style="display:${showFull ? '' : 'none'}">${escapeHtml(row.recognizer || '')}</td>
      <td class="rationale-col" style="display:${showFull ? '' : 'none'}">${escapeHtml(row.rationale || '')}</td>
    </tr>`).join('');
}

function renderSessions() {
  sessionCount.textContent = String(savedSessions.length);
  if (!savedSessions.length) {
    sessionList.innerHTML = '<div class="empty-inline">No saved sessions yet.</div>';
    return;
  }
  sessionList.innerHTML = savedSessions.map((session) => `
    <button type="button" class="session-item" data-session-id="${escapeHtml(session.id)}">
      <strong>${escapeHtml(session.title)}</strong>
      <span>${escapeHtml(session.operator)} · ${escapeHtml(session.entities)} entities</span>
      <small>${escapeHtml(session.createdAt)}</small>
    </button>`).join('');
}

function resetOutputs() {
  lastResult = null;
  renderSegments(originalPreview, [], 'original', 'Your original text will appear here after analysis.');
  renderSegments(resultPreview, [], 'result', 'The anonymized preview will appear here after analysis.');
  finalOutput.textContent = 'The final output text will appear here after analysis.';
  outputModeLabel.textContent = 'Ready for TXT download';
  kpiTotal.textContent = '0';
  kpiBand.textContent = 'N/A';
  kpiConfidence.textContent = '0%';
  kpiLow.textContent = '0';
  renderTags(entityMix, [], 'No entities yet.');
  renderTags(bandMix, [], 'No confidence data yet.');
  renderEntityBars({});
  renderEntityTable([]);
  downloadTextBtn.disabled = true;
  downloadEntitiesBtn.disabled = true;
  saveSessionBtn.disabled = true;
  synthNote.textContent = '';
}

function renderResponse(data) {
  lastResult = data;
  renderSegments(originalPreview, data.originalSegments, 'original', 'No source text available.');
  renderSegments(resultPreview, data.resultSegments, 'result', 'No result preview available.');
  attachLinkedHover();

  finalOutput.textContent = data.displayResultText || data.resultText || '';
  outputModeLabel.textContent = data.operator === 'synthesize'
    ? 'Final output includes synthesized text'
    : data.action === 'analyze'
      ? 'Preview uses the selected anonymization operator'
      : 'Final output from anonymize';

  kpiTotal.textContent = data.summary.totalEntities;
  kpiBand.textContent = data.summary.dominantBand;
  kpiConfidence.textContent = `${data.summary.averageConfidence}%`;
  kpiLow.textContent = String(data.summary.lowConfidenceCount || 0);

  const entityEntries = Object.entries(data.summary.entityCounts || {}).map(([key, value]) => `${key}: ${value}`);
  const bandEntries = Object.entries(data.summary.bandCounts || {}).map(([key, value]) => `${key}: ${value}`);
  renderTags(entityMix, entityEntries, 'No entities detected.');
  renderTags(bandMix, bandEntries, 'No confidence data available.');
  renderEntityBars(data.summary.entityCounts || {});
  renderEntityTable(data.entities || []);

  downloadTextBtn.disabled = !(data.resultText || data.displayResultText);
  downloadEntitiesBtn.disabled = !(data.entities && data.entities.length);
  saveSessionBtn.disabled = false;
  synthNote.textContent = data.synthNote || '';
  if (data.model && data.model.status) {
    spacyStatus.textContent = data.model.status;
  }
}

async function runAction(action) {
  const button = action === 'analyze' ? analyzeBtn : anonymizeBtn;
  const originalText = button.textContent;
  button.disabled = true;
  clearMessage();
  button.textContent = action === 'analyze' ? 'Detecting...' : 'Working...';

  try {
    const payload = new FormData();
    payload.set('text', textInput.value);
    if (fileInput.files[0]) payload.set('file', fileInput.files[0]);
    payload.set('threshold', thresholdInput.value);
    payload.set('operator', operatorSelect.value);
    payload.set('allowlist', valueOf('allowlist-input'));
    payload.set('denylist', valueOf('denylist-input'));
    payload.set('ner_model', nerModel.value);
    payload.set('show_rationale', showRationale.checked ? 'true' : 'false');
    payload.set('synth_provider', synthProvider.value);
    payload.set('synth_model', valueOf('synth-model', 'gpt-4o-mini'));
    payload.set('synth_deployment', valueOf('synth-deployment', ''));
    payload.set('synth_api_base', valueOf('synth-api-base', ''));
    payload.set('synth_api_version', valueOf('synth-api-version', '2024-08-01-preview'));
    payload.set('synth_api_key', valueOf('synth-api-key', ''));
    payload.set('synth_temperature', valueOf('synth-temperature', '0.2'));
    payload.set('synth_max_tokens', valueOf('synth-max-tokens', '800'));
    document.querySelectorAll('input[name="entities"]:checked').forEach((box) => payload.append('entities', box.value));

    const response = await fetch(apiUrl(`/api/${action}`), { method: 'POST', body: payload });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || `${action} failed.`);
    renderResponse(data);
    showMessage(`${action === 'analyze' ? 'Detection' : 'Anonymization'} complete. ${data.summary.totalEntities} entities found.`, 'success');
    if (data.synthNote) showMessage(data.synthNote, 'info');
  } catch (error) {
    showMessage(error.message || 'Something went wrong.', 'error');
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}

async function downloadViaPost(path, payload, fallbackName) {
  const response = await fetch(apiUrl(path), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Download failed.');
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  const disposition = response.headers.get('Content-Disposition') || '';
  const match = disposition.match(/filename="?([^";]+)"?/i);
  link.href = url;
  link.download = match ? match[1] : fallbackName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

async function refreshSessions() {
  try {
    const response = await fetch(apiUrl('/api/sessions'));
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || 'Unable to load sessions.');
    savedSessions = data.sessions || [];
    renderSessions();
  } catch (error) {
    showMessage(error.message || 'Unable to refresh sessions.', 'error');
  }
}

async function saveSession() {
  if (!lastResult) return;
  const title = prompt('Session title', `Hybrid ${lastResult.action === 'analyze' ? 'Detection' : 'Anonymize'} Session`);
  if (title === null) return;
  try {
    const payload = {
      title: title || 'Hybrid Analyze Session',
      sourceText: lastResult.sourceText || textInput.value,
      resultText: lastResult.displayResultText || lastResult.resultText || '',
      operator: lastResult.operator,
      summary: lastResult.summary,
      entityRows: lastResult.entities || [],
      pipelineCardId: pipelineCard.value || '',
      processingMs: 0,
      fileName: fileInput.files[0] ? fileInput.files[0].name : '',
    };
    const response = await fetch(apiUrl('/api/sessions'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || 'Save failed.');
    savedSessions = data.sessions || savedSessions;
    renderSessions();
    showMessage('Session saved successfully.', 'success');
  } catch (error) {
    showMessage(error.message || 'Save failed.', 'error');
  }
}

async function loadSession(sessionId) {
  try {
    const response = await fetch(apiUrl(`/api/sessions/${sessionId}`));
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || 'Session load failed.');
    const session = data.session;
    textInput.value = session.originalText || '';
    lastResult = {
      sourceText: session.originalText || '',
      displayResultText: session.anonymizedText || '',
      resultText: session.anonymizedText || '',
      linkedResultText: session.anonymizedText || '',
      entities: session.entityRows || [],
      originalSegments: [],
      resultSegments: [],
      action: 'anonymize',
      operator: session.operator || 'replace',
      summary: {
        totalEntities: session.entities || 0,
        entityCounts: session.entityCounts || {},
        dominantBand: 'Loaded',
        averageConfidence: (session.entityRows || []).length
          ? Math.round((session.entityRows || []).reduce((sum, row) => sum + Number(row.confidence || 0), 0) / (session.entityRows || []).length)
          : 0,
        lowConfidenceCount: (session.entityRows || []).filter((row) => Number(row.confidence || 0) < 50).length,
        bandCounts: (session.entityRows || []).reduce((acc, row) => {
          const key = row.confidenceBand || 'Unknown';
          acc[key] = (acc[key] || 0) + 1;
          return acc;
        }, {}),
      },
    };
    originalPreview.textContent = session.originalText || '';
    originalPreview.classList.remove('empty-state-box');
    resultPreview.textContent = session.anonymizedText || '';
    resultPreview.classList.remove('empty-state-box');
    finalOutput.textContent = session.anonymizedText || '';
    renderResponse(lastResult);
    showMessage(`Loaded session: ${session.title}`, 'success');
  } catch (error) {
    showMessage(error.message || 'Unable to load session.', 'error');
  }
}

function updateProviderFields() {
  const provider = synthProvider.value;
  providerFields.forEach((field) => field.classList.add('hidden'));
  if (provider === 'openai') {
    document.querySelectorAll('.openai-auth, .endpoint-field').forEach((field) => field.classList.remove('hidden'));
  } else if (provider === 'azure_openai') {
    document.querySelectorAll('.azure-only, .endpoint-field, .openai-auth').forEach((field) => field.classList.remove('hidden'));
  }
}

async function changeModel() {
  try {
    const response = await fetch(apiUrl('/api/model'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ choice: nerModel.value }),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || 'Model change failed.');
    spacyStatus.textContent = data.model.status || 'Model updated.';
    showMessage(`NER model updated to ${data.model.resolved}.`, 'info');
  } catch (error) {
    showMessage(error.message || 'Model change failed.', 'error');
  }
}

selectAllBtn.addEventListener('click', () => setCheckboxes(true));
clearAllBtn.addEventListener('click', () => setCheckboxes(false));
loadSampleBtn.addEventListener('click', () => { textInput.value = SAMPLE_TEXT; });
clearBtn.addEventListener('click', () => {
  textInput.value = '';
  fileInput.value = '';
  setCheckboxes(true);
  resetOutputs();
  clearMessage();
});
analyzeBtn.addEventListener('click', () => runAction('analyze'));
anonymizeBtn.addEventListener('click', () => runAction('anonymize'));
downloadTextBtn.addEventListener('click', async () => {
  if (!lastResult) return;
  try {
    await downloadViaPost('/api/download/text', {
      text: lastResult.displayResultText || lastResult.resultText || '',
      filename: 'hybrid_anonymized_output.txt',
    }, 'hybrid_anonymized_output.txt');
  } catch (error) {
    showMessage(error.message, 'error');
  }
});
downloadEntitiesBtn.addEventListener('click', async () => {
  if (!lastResult) return;
  try {
    await downloadViaPost('/api/download/entities', { rows: lastResult.entities || [] }, 'hybrid_entity_evidence.csv');
  } catch (error) {
    showMessage(error.message, 'error');
  }
});
saveSessionBtn.addEventListener('click', saveSession);
refreshSessionsBtn.addEventListener('click', refreshSessions);
thresholdInput.addEventListener('input', setThresholdLabel);
showRationale.addEventListener('change', () => renderEntityTable((lastResult && lastResult.entities) || []));
toggleAdvancedBtn.addEventListener('click', () => advancedDrawer.classList.remove('hidden'));
closeAdvancedBtn.addEventListener('click', () => advancedDrawer.classList.add('hidden'));
advancedDrawer.addEventListener('click', (event) => { if (event.target === advancedDrawer) advancedDrawer.classList.add('hidden'); });
operatorSelect.addEventListener('change', updateProviderFields);
synthProvider.addEventListener('change', updateProviderFields);
nerModel.addEventListener('change', changeModel);
sessionList.addEventListener('click', async (event) => {
  const button = event.target.closest('.session-item');
  if (!button) return;
  await loadSession(button.dataset.sessionId);
});


initSidebarState();
if (navToggleBtn) {
  navToggleBtn.addEventListener('click', () => {
    const expanded = !hybridShell.classList.contains('is-expanded');
    applySidebarState(expanded);
    window.localStorage.setItem(SIDEBAR_STORAGE_KEY, expanded ? 'true' : 'false');
  });
}
setThresholdLabel();
updateProviderFields();
renderSessions();
resetOutputs();
