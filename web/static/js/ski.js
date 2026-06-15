(function () {
  'use strict';

  const form        = document.getElementById('ski-form');
  const resultsEl   = document.getElementById('results-container');
  const downloadBtn = document.getElementById('download-btn');
  let lastParams    = '';
  let lastSearch    = { region: '', name: '' };  // 使用者本次搜尋輸入的參數
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
              <th scope="col" class="text-center">收藏</th>
            </tr>
          </thead>
          <tbody id="results-tbody"></tbody>
        </table>
      </div>`;
  }

  // 用 data-* 把該列的資料完整序列化到按鈕上，等 click 才送 /api/favorites
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
    // 收藏 payload — location = 雪場+地區、time = 雪季
    const favPayload = {
      type: 'ski',
      location: `${r.resort ?? ''} ${r.region ?? ''}`.trim() || '未命名雪場',
      time: r.season || (lastSearch.region || lastSearch.name || '未知雪季'),
      params: { ...lastSearch },
      data: {
        resort: r.resort ?? '',
        region: r.region ?? '',
        ticket_type: r.ticket_type ?? '',
        ticket_type_zh: r.ticket_type_zh ?? '',
        price: r.price ?? '',
        season: r.season ?? '',
        source_url: r.source_url ?? '',
      },
      label: `${r.resort ?? ''}・${r.ticket_type_zh || r.ticket_type || ''}`.trim(),
    };
    const favJson = escHtml(JSON.stringify(favPayload));
    tbody.insertAdjacentHTML('beforeend', `
      <tr>
        <td class="fw-semibold">${escHtml(r.resort ?? '')}</td>
        <td><span class="badge region-badge-${escHtml(r.region ?? '')}">${escHtml(r.region ?? '')}</span></td>
        <td class="small">${escHtml(r.ticket_type ?? '')}</td>
        <td>${escHtml(r.ticket_type_zh ?? '')}</td>
        <td class="fw-bold">${escHtml(r.price ?? '')}</td>
        <td>${escHtml(r.season ?? '')}</td>
        <td>${link}</td>
        <td class="text-center">
          <button type="button" class="btn btn-outline-danger btn-sm py-0 fav-btn"
                  data-fav="${favJson}" title="加入收藏" aria-label="加入收藏">
            <i class="bi bi-heart" aria-hidden="true"></i>
          </button>
        </td>
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
    lastSearch  = { region, name };  // 保存使用者輸入，給收藏用

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

  // 收藏按鈕（事件代理 — 動態新增的 row 也適用）
  resultsEl.addEventListener('click', async (ev) => {
    const btn = ev.target.closest('.fav-btn');
    if (!btn) return;
    const payload = JSON.parse(btn.dataset.fav);
    btn.disabled = true;
    try {
      const res = await fetch('/api/favorites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.status === 401) {
        if (confirm('請先登入才能收藏。前往登入頁？')) location.href = '/login?next=/ski';
        btn.disabled = false;
        return;
      }
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || '收藏失敗');
      // 視覺反饋：愛心填滿 + 變紅
      btn.classList.remove('btn-outline-danger');
      btn.classList.add('btn-danger');
      btn.innerHTML = '<i class="bi bi-heart-fill" aria-hidden="true"></i>';
      btn.title = `已收藏（id=${json.id}）— 至我的帳號查看`;
      btn.setAttribute('aria-label', '已收藏');
    } catch (err) {
      alert('收藏失敗：' + err.message);
      btn.disabled = false;
    }
  });
})();
