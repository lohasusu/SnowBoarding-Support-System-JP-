(function () {
  'use strict';

  const form        = document.getElementById('ski-form');
  const resultsEl   = document.getElementById('results-container');
  const downloadBtn = document.getElementById('download-btn');
  let lastParams    = '';
  let eventSource   = null;
  let resultCount   = 0;
  let resortTotal   = 0;
  let resortDone    = 0;

  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function setQuerying(on) {
    form.querySelector('[type=submit]').disabled = on;
    if (!on) {
      downloadBtn.disabled     = resultCount === 0;
      downloadBtn.ariaDisabled = String(resultCount === 0);
    } else {
      downloadBtn.disabled     = true;
      downloadBtn.ariaDisabled = 'true';
    }
  }

  function initTable() {
    resultsEl.innerHTML = `
      <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
        <h2 id="results-heading" class="h5 mb-0 fw-bold">
          查詢結果 <span id="result-count" class="badge bg-primary ms-1">0 筆</span>
        </h2>
        <small id="resort-progress" class="text-muted"></small>
      </div>
      <div class="results-table-wrap">
        <table class="table table-hover table-striped align-middle">
          <thead class="table-dark">
            <tr>
              <th scope="col">雪場</th>
              <th scope="col">地區</th>
              <th scope="col">票種（日文）</th>
              <th scope="col">票種（中文）</th>
              <th scope="col">票價</th>
              <th scope="col">雪季</th>
              <th scope="col">官網</th>
            </tr>
          </thead>
          <tbody id="results-tbody"></tbody>
        </table>
      </div>`;
  }

  function appendRow(r) {
    const tbody = document.getElementById('results-tbody');
    if (!tbody) return;
    const link = r.source_url
      ? `<a href="${escHtml(r.source_url)}" target="_blank" rel="noopener noreferrer"
            class="btn btn-outline-secondary btn-sm py-0"
            aria-label="${escHtml(r.resort)} 票價頁">
           <i class="bi bi-box-arrow-up-right" aria-hidden="true"></i>
         </a>`
      : '—';
    tbody.insertAdjacentHTML('beforeend', `
      <tr>
        <td class="fw-semibold">${escHtml(r.resort ?? '')}</td>
        <td><span class="badge region-badge-${escHtml(r.region ?? '')}">${escHtml(r.region ?? '')}</span></td>
        <td class="small">${escHtml(r.ticket_type ?? '')}</td>
        <td>${escHtml(r.ticket_type_zh ?? '')}</td>
        <td class="fw-bold">${escHtml(r.price ?? '')}</td>
        <td>${escHtml(r.season ?? '')}</td>
        <td>${link}</td>
      </tr>`);
  }

  function updateProgress() {
    const countEl = document.getElementById('result-count');
    if (countEl) countEl.textContent = `${resultCount} 筆`;
    const progEl = document.getElementById('resort-progress');
    if (progEl && resortTotal > 0) {
      progEl.textContent = `已掃描 ${resortDone} / ${resortTotal} 個雪場`;
    }
  }

  function setError(msg) {
    resultsEl.innerHTML = `
      <div class="alert alert-danger d-flex align-items-center gap-2" role="alert">
        <i class="bi bi-exclamation-triangle-fill flex-shrink-0" aria-hidden="true"></i>
        <div>查詢失敗：${escHtml(msg)}</div>
      </div>`;
  }

  function showEmpty() {
    resultsEl.innerHTML = `
      <div class="alert alert-warning d-flex align-items-center gap-2" role="alert">
        <i class="bi bi-info-circle-fill flex-shrink-0" aria-hidden="true"></i>
        <div>沒有找到符合條件的資料，請嘗試其他地區或名稱。</div>
      </div>`;
  }

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }

    const region = document.getElementById('region').value;
    const name   = document.getElementById('ski-name').value.trim();
    const params = new URLSearchParams();
    if (region) params.append('region', region);
    if (name)   params.append('name', name);
    lastParams  = params.toString();

    setQuerying(true);
    resultCount = 0;
    resortTotal = 0;
    resortDone  = 0;

    resultsEl.innerHTML = `
      <div class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">查詢中...</span>
        </div>
        <p class="mt-3 text-muted">正在連線抓取票價，請稍候…</p>
      </div>`;

    eventSource = new EventSource(`/api/ski/stream?${lastParams}`);

    eventSource.addEventListener('start', (ev) => {
      const { total } = JSON.parse(ev.data);
      resortTotal = total;
      initTable();
      updateProgress();
    });

    eventSource.addEventListener('result', (ev) => {
      const item = JSON.parse(ev.data);
      appendRow(item);
      resultCount++;
      updateProgress();
    });

    eventSource.addEventListener('resort_done', () => {
      resortDone++;
      updateProgress();
    });

    eventSource.addEventListener('done', () => {
      eventSource.close();
      eventSource = null;
      setQuerying(false);
      if (resultCount === 0) showEmpty();
    });

    eventSource.addEventListener('error', (ev) => {
      let msg = '連線中斷，請重試';
      try { msg = JSON.parse(ev.data).message; } catch (_) { /* use default */ }
      setError(msg);
      eventSource.close();
      eventSource = null;
      setQuerying(false);
    });

    eventSource.onerror = () => {
      if (eventSource && eventSource.readyState === EventSource.CLOSED) {
        if (resultCount === 0) setError('連線中斷，請重試');
        setQuerying(false);
        eventSource = null;
      }
    };
  });

  downloadBtn.addEventListener('click', () => {
    window.location.href = `/api/ski/download?${lastParams}`;
  });
})();
