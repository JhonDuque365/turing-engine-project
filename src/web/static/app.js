/* ============================================================
   Motor Genérico de Máquina de Turing – Frontend JavaScript
   Universidad de Pamplona 2026-1
   ============================================================ */

let selectedFile = null;
let isRunning    = false;
let traceRows    = [];

// ---- Seleccionar máquina -----------------------------------------------
function selectMachine(file) {
  selectedFile = file;
  document.querySelectorAll('.machine-btn').forEach(b => b.classList.remove('active'));
  const btn = document.querySelector(`[data-file="${file}"]`);
  if (btn) btn.classList.add('active');

  // Mostrar info rápida
  fetch('/api/machines')
    .then(r => r.json())
    .then(machines => {
      const m = machines.find(x => x.file === file);
      if (!m) return;
      const info = document.getElementById('machine-info');
      const modeClass = `mode-${m.mode}`;
      info.innerHTML = `
        <div class="info-row"><span class="info-key">Nombre:</span><span>${m.name}</span></div>
        <div class="info-row"><span class="info-key">Modo:</span>
          <span class="mode-badge ${modeClass}">${m.mode}</span></div>
        <div class="info-row"><span class="info-key">Estados:</span><span>${m.states_count}</span></div>
        <div class="info-row"><span class="info-key">Transiciones:</span><span>${m.transitions_count}</span></div>
        <div class="info-row"><span class="info-key">Pruebas:</span><span>${m.tests_count}</span></div>
        ${m.description ? `<div style="margin-top:8px;font-size:0.79rem;color:#666;font-style:italic">${m.description}</div>` : ''}
      `;
      document.getElementById('machine-info-card').style.display = 'block';
    });
}

// ---- Cargar máquina e inicializar --------------------------------------
function loadAndInit() {
  if (!selectedFile) { alert('Selecciona una máquina primero.'); return; }
  const input = document.getElementById('input-string').value;
  clearTrace();
  resetResultBadge();

  fetch('/api/load', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file: selectedFile, input })
  })
  .then(r => r.json())
  .then(data => {
    if (data.error) { showError(data.error); return; }

    updateState(data.current.state, null, data.machine);
    updateTape(data.current.tape);
    setStepCount(0);
    setTransition('(inicio)');

    // Tabla delta
    buildDeltaTable(data.transitions);

    // Habilitar botones
    setButtons(true);

    // Agregar fila inicial a traza
    addTraceRow(0, data.current.state, data.current.head_symbol, '(inicio)');

    document.getElementById('tests-card').style.display = 'block';
    document.getElementById('metrics-card').style.display = 'none';
  })
  .catch(err => showError(err.toString()));
}

// ---- Paso a paso -------------------------------------------------------
function doStep() {
  if (isRunning) return;
  fetch('/api/step', { method: 'POST' })
  .then(r => r.json())
  .then(data => {
    if (data.error) { showError(data.error); return; }
    const cfg = data.current;

    updateState(cfg.state, data.status, null);
    updateTape(cfg.tape);
    setStepCount(data.step_count);
    setTransition(cfg.transition);
    addTraceRow(cfg.step, cfg.state, cfg.head_symbol, cfg.transition);

    if (data.done) {
      showResult(data.status);
      showMetrics(data.metrics);
      document.getElementById('btn-step').disabled = true;
      document.getElementById('btn-run').disabled  = true;
    }
  })
  .catch(err => showError(err.toString()));
}

// ---- Ejecutar completo -------------------------------------------------
function doRun() {
  if (isRunning) return;
  isRunning = true;
  const maxSteps = parseInt(document.getElementById('max-steps').value) || 10000;

  fetch('/api/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ max_steps: maxSteps })
  })
  .then(r => r.json())
  .then(data => {
    isRunning = false;
    if (data.error) { showError(data.error); return; }

    const cfg = data.current;
    updateState(cfg.state, data.result, null);
    updateTape(data.tape);
    setStepCount(data.step_count);
    setTransition(cfg.transition);

    // Reconstruir traza completa
    clearTrace();
    data.trace.forEach(c => addTraceRow(c.step, c.state, c.head_symbol, c.transition));

    showResult(data.result);
    showMetrics(data.metrics);
    document.getElementById('btn-step').disabled = true;
    document.getElementById('btn-run').disabled  = true;
  })
  .catch(err => { isRunning = false; showError(err.toString()); });
}

// ---- Reiniciar ---------------------------------------------------------
function doReset() {
  const input = document.getElementById('input-string').value;
  clearTrace();
  resetResultBadge();

  fetch('/api/reset', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ input })
  })
  .then(r => r.json())
  .then(data => {
    if (data.error) { showError(data.error); return; }
    const cfg = data.current;
    updateState(cfg.state, null, null);
    updateTape(cfg.tape);
    setStepCount(0);
    setTransition('(inicio)');
    setButtons(true);
    document.getElementById('metrics-card').style.display = 'none';
    addTraceRow(0, cfg.state, cfg.head_symbol, '(inicio)');
  })
  .catch(err => showError(err.toString()));
}

// ---- Suite de pruebas --------------------------------------------------
function runTests() {
  fetch('/api/tests', { method: 'POST' })
  .then(r => r.json())
  .then(data => {
    if (data.error) { showError(data.error); return; }
    const container = document.getElementById('tests-content');
    let html = `<div class="tests-summary">${data.passed}/${data.total} pruebas pasadas</div>`;
    data.results.forEach(r => {
      const cls  = r.passed ? 'pass' : 'fail';
      const icon = r.passed ? '✅' : '❌';
      const inp  = r.input === "''" ? 'ε (vacía)' : r.input;
      html += `<div class="test-row ${cls}">
        <span class="test-icon">${icon}</span>
        <span class="test-input">${inp}</span>
        <span class="test-expected">→ ${r.expected}</span>
        <span class="test-actual">${r.actual}</span>
      </div>`;
    });
    container.innerHTML = html;
  })
  .catch(err => showError(err.toString()));
}

// ---- Helpers de UI -----------------------------------------------------

function updateTape(cells) {
  const container = document.getElementById('tape-container');
  if (!cells || cells.length === 0) return;
  container.innerHTML = '';
  cells.forEach(cell => {
    const isHead   = cell.is_head;
    const isMarked = ['X','Y'].includes(cell.symbol);
    const div = document.createElement('div');
    div.className = 'tape-cell';
    div.innerHTML = `
      <div class="cell-arrow ${isHead ? 'visible' : ''}">&#9650;</div>
      <div class="cell-box ${isHead ? 'is-head' : ''} ${isMarked && !isHead ? 'marked' : ''}">${cell.symbol}</div>
    `;
    container.appendChild(div);
  });
  // Scroll al cabezal
  const headEl = container.querySelector('.is-head');
  if (headEl) headEl.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
}

function updateState(state, status, machineName) {
  const badge = document.getElementById('state-badge');
  const name  = document.getElementById('state-name');
  badge.className = 'state-badge';
  if (status === 'accept') badge.classList.add('accept');
  if (status === 'reject') badge.classList.add('reject');
  badge.textContent = state;
  name.textContent  = state;
  if (machineName) name.textContent += ` — ${machineName}`;
}

function setStepCount(n) {
  document.getElementById('step-number').textContent = n;
}

function setTransition(t) {
  document.getElementById('transition-text').textContent = t;
}

function showResult(result) {
  const badge = document.getElementById('result-badge');
  badge.style.display = 'block';
  badge.className = 'result-badge';
  if (result === 'accept') {
    badge.classList.add('accept');
    badge.textContent = '✓ ACCEPT';
  } else if (result === 'reject') {
    badge.classList.add('reject');
    badge.textContent = '✗ REJECT';
  } else {
    badge.classList.add('timeout');
    badge.textContent = '⏱ TIMEOUT';
  }
}

function resetResultBadge() {
  const badge = document.getElementById('result-badge');
  badge.style.display = 'none';
  badge.className = 'result-badge';
  badge.textContent = '';
}

function showMetrics(m) {
  if (!m) return;
  const card = document.getElementById('metrics-card');
  const content = document.getElementById('metrics-content');
  const entries = [
    ['Resultado',         m.resultado],
    ['Pasos',            m.pasos_ejecutados],
    ['Celdas visitadas', m.celdas_visitadas],
    ['Mov. derecha',     m.movimientos_derecha],
    ['Mov. izquierda',   m.movimientos_izquierda],
    ['Celdas no blancas',m.celdas_no_blancas],
    ['Cinta final',      m.cinta_final],
  ];
  content.innerHTML = `<div class="metrics-grid">${
    entries.map(([k,v]) => `<div class="metric-item"><div class="metric-key">${k}</div><div class="metric-val">${v}</div></div>`).join('')
  }</div>`;
  card.style.display = 'block';
}

function addTraceRow(step, state, symbol, transition) {
  const tbody = document.getElementById('trace-body');
  // Limpiar placeholder
  if (tbody.querySelector('.trace-empty')) tbody.innerHTML = '';

  const tr = document.createElement('tr');
  const isAccept = state.toLowerCase().includes('accept');
  const isReject = state.toLowerCase().includes('reject');
  if (isAccept) tr.classList.add('accept-row');
  if (isReject) tr.classList.add('reject-row');
  tr.innerHTML = `
    <td>${step}</td>
    <td>${state}</td>
    <td>${symbol}</td>
    <td>${transition}</td>
  `;
  tbody.appendChild(tr);
  tbody.parentElement.scrollTop = tbody.parentElement.scrollHeight;
}

function clearTrace() {
  const tbody = document.getElementById('trace-body');
  tbody.innerHTML = '<tr><td colspan="4" class="trace-empty">Aquí aparecerá la traza de ejecución.</td></tr>';
}

function buildDeltaTable(transitions) {
  const tbody = document.getElementById('delta-body');
  tbody.innerHTML = '';
  transitions.sort((a,b) => a.from.localeCompare(b.from) || a.read.localeCompare(b.read))
  .forEach(t => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${t.from}</td><td>${t.read}</td><td>${t.write}</td><td>${t.move}</td><td>${t.to}</td>`;
    tbody.appendChild(tr);
  });
  document.getElementById('delta-card').style.display = 'block';
}

function setButtons(loaded) {
  document.getElementById('btn-step').disabled  = !loaded;
  document.getElementById('btn-run').disabled   = !loaded;
  document.getElementById('btn-reset').disabled = !loaded;
}

function showError(msg) {
  alert('⚠️ Error: ' + msg);
}
