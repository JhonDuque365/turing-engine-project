/* ================================================================
   Motor Genérico de Máquina de Turing – Frontend
   Universidad de Pamplona 2026-1
   ================================================================ */

let selectedFile = null;
let isRunning    = false;

// ---- Seleccionar máquina -----------------------------------------------
function selectMachine(file) {
  selectedFile = file;
  document.querySelectorAll('.machine-btn').forEach(b => b.classList.remove('active'));
  const btn = document.querySelector(`[data-file="${file}"]`);
  if (btn) btn.classList.add('active');
  fetch('/api/machines')
    .then(r => r.json())
    .then(machines => {
      const m = machines.find(x => x.file === file);
      if (!m) return;
      const info = document.getElementById('machine-info');
      info.innerHTML = `
        <div class="info-row"><span class="info-key">Nombre:</span><span>${m.name}</span></div>
        <div class="info-row"><span class="info-key">Modo:</span>
          <span class="mode-badge mode-${m.mode}">${m.mode}</span></div>
        <div class="info-row"><span class="info-key">Estados:</span><span>${m.states_count}</span></div>
        <div class="info-row"><span class="info-key">Transiciones:</span><span>${m.transitions_count}</span></div>
        <div class="info-row"><span class="info-key">Pruebas:</span><span>${m.tests_count}</span></div>
        ${m.imported ? '<div style="margin-top:6px"><span style="background:#fff3cd;padding:2px 8px;border-radius:10px;font-size:0.78rem;color:#856404">📤 Importada externamente</span></div>' : ''}
        ${m.description ? `<div style="margin-top:8px;font-size:0.79rem;color:#666;font-style:italic">${m.description}</div>` : ''}
      `;
      document.getElementById('machine-info-card').style.display = 'block';
    });
}

// ================================================================
// IMPORTAR MÁQUINA CON VALIDACIÓN
// ================================================================
function importMachine(event) {
  const file = event.target.files[0];
  if (!file) return;

  // Limpiar el input para que el mismo archivo pueda reimportarse
  event.target.value = '';

  const reader = new FileReader();
  reader.onload = function(e) {
    const content  = e.target.result;
    const filename = file.name;

    // Pre-validación en frontend: JSON sintaxis
    let parsed;
    try {
      parsed = JSON.parse(content);
    } catch(err) {
      showModal('error',
        '❌ Error de sintaxis JSON',
        `<p>El archivo <strong>${filename}</strong> no es un JSON válido.</p>
         <div class="modal-section-title">Detalle del error</div>
         <div class="modal-error-item">${err.message}</div>
         <p style="margin-top:10px;font-size:0.82rem;color:#555">Verifica que el archivo tenga llaves, corchetes y comas correctamente colocados.</p>`
      );
      return;
    }

    // Enviar al servidor para validación formal
    fetch('/api/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, filename })
    })
    .then(r => r.json())
    .then(data => {
      if (!data.ok) {
        // Construir modal de error detallado
        let body = `<p>El archivo <strong>${filename}</strong> no pasó la validación formal.</p>`;

        if (data.details && data.details.length > 0) {
          body += `<div class="modal-section-title">❌ Errores encontrados (${data.details.length})</div>`;
          data.details.forEach(d => {
            body += `<div class="modal-error-item">${d}</div>`;
          });
        }
        if (data.warnings && data.warnings.length > 0) {
          body += `<div class="modal-section-title">⚠️ Advertencias</div>`;
          data.warnings.forEach(w => {
            body += `<div class="modal-warning-item">${w}</div>`;
          });
        }
        body += `<p style="margin-top:12px;font-size:0.82rem;color:#555">Corrige los errores y vuelve a importar el archivo.</p>`;
        showModal('error', '❌ Validación fallida', body);
        return;
      }

      // Éxito: construir modal de confirmación
      let body = `<p>La máquina fue validada y guardada correctamente.</p>
        <div class="modal-success-info">
          <div class="modal-info-chip"><b>Nombre:</b> ${data.name}</div>
          <div class="modal-info-chip"><b>Modo:</b> ${data.mode}</div>
          <div class="modal-info-chip"><b>Estados:</b> ${data.states_count}</div>
          <div class="modal-info-chip"><b>Transiciones:</b> ${data.transitions_count}</div>
          <div class="modal-info-chip"><b>Archivo:</b> ${data.filename}</div>
        </div>`;

      if (data.warnings && data.warnings.length > 0) {
        body += `<div class="modal-section-title">⚠️ Avisos</div>`;
        data.warnings.forEach(w => {
          body += `<div class="modal-warning-item">${w}</div>`;
        });
      }

      showModal('success', '✅ Máquina importada', body);

      // Agregar botón a la lista y seleccionarla automáticamente
      addMachineButton(data.filename, true);
      selectedFile = data.filename;
      selectMachine(data.filename);
    })
    .catch(err => showModal('error', '❌ Error de red', `<p>${err.toString()}</p>`));
  };
  reader.readAsText(file);
}

function addMachineButton(filename, imported = false) {
  const list = document.getElementById('machine-list');
  // Evitar duplicados
  if (document.querySelector(`[data-file="${filename}"]`)) return;
  const btn = document.createElement('button');
  btn.className = 'machine-btn' + (imported ? ' imported' : '');
  btn.dataset.file = filename;
  btn.textContent  = filename;
  btn.onclick = () => selectMachine(filename);
  list.appendChild(btn);
}

// ================================================================
// MODAL
// ================================================================
function showModal(type, title, bodyHtml) {
  const modal  = document.getElementById('import-modal');
  const header = document.getElementById('modal-header');
  const icon   = document.getElementById('modal-icon');
  const titleEl= document.getElementById('modal-title');
  const body   = document.getElementById('modal-body');

  header.className = `modal-header ${type}`;
  icon.textContent  = type === 'success' ? '✅' : type === 'warning' ? '⚠️' : '❌';
  titleEl.textContent = title;
  body.innerHTML = bodyHtml;
  modal.style.display = 'flex';
}

function closeModal() {
  document.getElementById('import-modal').style.display = 'none';
}

// Cerrar modal al clic en el fondo
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('import-modal').addEventListener('click', function(e) {
    if (e.target === this) closeModal();
  });
});

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
    if (data.error) { showModal('error', '❌ Error al cargar', `<p>${data.error}</p>`); return; }
    updateState(data.current.state, null, data.machine);
    updateTape(data.current.tape);
    setStepCount(0);
    setTransition('(inicio)');
    buildDeltaTable(data.transitions);
    setButtons(true);
    addTraceRow(0, data.current.state, data.current.head_symbol, '(inicio)');
    document.getElementById('tests-card').style.display = 'block';
    document.getElementById('metrics-card').style.display = 'none';
  })
  .catch(err => showModal('error', '❌ Error', `<p>${err.toString()}</p>`));
}

// ---- Paso a paso -------------------------------------------------------
function doStep() {
  if (isRunning) return;
  fetch('/api/step', { method: 'POST' })
  .then(r => r.json())
  .then(data => {
    if (data.error) { showModal('error', '❌ Error', `<p>${data.error}</p>`); return; }
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
  .catch(err => showModal('error', '❌ Error', `<p>${err.toString()}</p>`));
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
    if (data.error) { showModal('error', '❌ Error', `<p>${data.error}</p>`); return; }
    updateState(data.current.state, data.result, null);
    updateTape(data.tape);
    setStepCount(data.step_count);
    setTransition(data.current.transition);
    clearTrace();
    data.trace.forEach(c => addTraceRow(c.step, c.state, c.head_symbol, c.transition));
    showResult(data.result);
    showMetrics(data.metrics);
    document.getElementById('btn-step').disabled = true;
    document.getElementById('btn-run').disabled  = true;
  })
  .catch(err => { isRunning = false; showModal('error', '❌ Error', `<p>${err.toString()}</p>`); });
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
    if (data.error) { showModal('error', '❌ Error', `<p>${data.error}</p>`); return; }
    updateState(data.current.state, null, null);
    updateTape(data.current.tape);
    setStepCount(0);
    setTransition('(inicio)');
    setButtons(true);
    document.getElementById('metrics-card').style.display = 'none';
    addTraceRow(0, data.current.state, data.current.head_symbol, '(inicio)');
  })
  .catch(err => showModal('error', '❌ Error', `<p>${err.toString()}</p>`));
}

// ---- Suite de pruebas --------------------------------------------------
function runTests() {
  fetch('/api/tests', { method: 'POST' })
  .then(r => r.json())
  .then(data => {
    if (data.error) { showModal('error', '❌ Error', `<p>${data.error}</p>`); return; }
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
  });
}

// ---- Helpers de UI -----------------------------------------------------
function updateTape(cells) {
  const container = document.getElementById('tape-container');
  if (!cells || cells.length === 0) return;
  container.innerHTML = '';
  cells.forEach(cell => {
    const isMarked = ['X','Y'].includes(cell.symbol);
    const div = document.createElement('div');
    div.className = 'tape-cell';
    div.innerHTML = `
      <div class="cell-arrow ${cell.is_head ? 'visible' : ''}">&#9650;</div>
      <div class="cell-box ${cell.is_head ? 'is-head' : ''} ${isMarked && !cell.is_head ? 'marked' : ''}">${cell.symbol}</div>
    `;
    container.appendChild(div);
  });
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
  name.textContent  = machineName ? `${state} — ${machineName}` : state;
}

function setStepCount(n) { document.getElementById('step-number').textContent = n; }
function setTransition(t) { document.getElementById('transition-text').textContent = t; }

function showResult(result) {
  const badge = document.getElementById('result-badge');
  badge.style.display = 'block';
  badge.className = 'result-badge';
  if (result === 'accept')  { badge.classList.add('accept');  badge.textContent = '✓ ACCEPT'; }
  else if (result === 'reject') { badge.classList.add('reject');  badge.textContent = '✗ REJECT'; }
  else { badge.classList.add('timeout'); badge.textContent = '⏱ TIMEOUT'; }
}

function resetResultBadge() {
  const badge = document.getElementById('result-badge');
  badge.style.display = 'none'; badge.className = 'result-badge'; badge.textContent = '';
}

function showMetrics(m) {
  if (!m) return;
  const entries = [
    ['Resultado', m.resultado], ['Pasos', m.pasos_ejecutados],
    ['Celdas visitadas', m.celdas_visitadas], ['Mov. derecha', m.movimientos_derecha],
    ['Mov. izquierda', m.movimientos_izquierda], ['Celdas no blancas', m.celdas_no_blancas],
    ['Cinta final', m.cinta_final],
  ];
  document.getElementById('metrics-content').innerHTML =
    `<div class="metrics-grid">${entries.map(([k,v]) =>
      `<div class="metric-item"><div class="metric-key">${k}</div><div class="metric-val">${v}</div></div>`
    ).join('')}</div>`;
  document.getElementById('metrics-card').style.display = 'block';
}

function addTraceRow(step, state, symbol, transition) {
  const tbody = document.getElementById('trace-body');
  if (tbody.querySelector('.trace-empty')) tbody.innerHTML = '';
  const tr = document.createElement('tr');
  if (state.toLowerCase().includes('accept')) tr.classList.add('accept-row');
  if (state.toLowerCase().includes('reject')) tr.classList.add('reject-row');
  tr.innerHTML = `<td>${step}</td><td>${state}</td><td>${symbol}</td><td>${transition}</td>`;
  tbody.appendChild(tr);
  tbody.parentElement.scrollTop = tbody.parentElement.scrollHeight;
}

function clearTrace() {
  document.getElementById('trace-body').innerHTML =
    '<tr><td colspan="4" class="trace-empty">Aquí aparecerá la traza de ejecución.</td></tr>';
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
