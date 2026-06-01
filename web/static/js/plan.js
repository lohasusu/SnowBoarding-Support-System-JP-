(function () {
  'use strict';

  const form      = document.getElementById('plan-form');
  const resultsEl = document.getElementById('plan-results');

  let lastFlights = [];
  let lastSki     = [];
  let lastMeta    = {};

  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function fmtTime(t) {
    if (!t || t === '—') return '—';
    return t.length > 10 ? t.slice(11, 16) : t;
  }

  function extractAirline(r) {
    if (r.airline_names && r.airline_names.length > 0) {
      return [...new Set(r.airline_names)].join(' / ');
    }
    return (r.flights_str || '')
      .split(' → ')
      .map(leg => leg.replace(/\s*\([A-Z]{3}→[A-Z]{3}\).*/, '').replace(/\s+[A-Z]{2}\s*\d+\s*$/, '').trim())
      .filter(Boolean).join(' / ') || '未知';
  }

  // 最小日期設定
  document.getElementById('plan-departure').min = new Date().toISOString().split('T')[0];
  document.getElementById('plan-departure').addEventListener('change', function () {
    document.getElementById('plan-return').min = this.value;
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const origin    = document.getElementById('plan-origin').value;
    const destEl    = document.getElementById('plan-dest');
    const dest      = destEl.value;
    const destName  = destEl.options[destEl.selectedIndex].dataset.name;
    const region    = document.getElementById('plan-region').value;
    const departure = document.getElementById('plan-departure').value;
    const retDate   = document.getElementById('plan-return').value;
    const adults    = document.getElementById('plan-adults').value;

    if (!departure) { alert('請輸入出發日期'); return; }

    lastMeta = { origin, destination: dest, dest_name: destName, region, departure, ret_date: retDate, adults: Number(adults) };

    form.querySelector('[type=submit]').disabled = true;
    showLoading();

    const flightParams = new URLSearchParams({ origin, destination: dest, dest_name: destName, departure, adults });
    if (retDate) flightParams.append('ret_date', retDate);

    const skiParams = new URLSearchParams();
    if (region) skiParams.append('region', region);

    try {
      const [flightRes, skiRes] = await Promise.all([
        fetch(`/api/flight/search?${flightParams}`).then(r => r.json()),
        fetch(`/api/ski/search?${skiParams}`).then(r => r.json()),
      ]);

      lastFlights = flightRes.ok ? sortFlights(flightRes.data) : [];
      lastSki     = skiRes.ok     ? skiRes.data : [];

      const flightErr = flightRes.ok ? '' : flightRes.error;
      const skiErr    = skiRes.ok    ? '' : skiRes.error;

      renderResults(lastFlights, lastSki, flightErr, skiErr, flightRes.backend || '');
    } catch (err) {
      resultsEl.innerHTML = `<div class="alert alert-danger">${escHtml(err.message)}</div>`;
    } finally {
      form.querySelector('[type=submit]').disabled = false;
    }
  });

  function sortFlights(data) {
    return [...data].sort((a, b) => {
      const ta = a.dep_time || '', tb = b.dep_time || '';
      if (ta !== tb) return ta < tb ? -1 : 1;
      return (a.price ?? 0) - (b.price ?? 0);
    });
  }

  function showLoading() {
    resultsEl.innerHTML = `
      <div class="text-center py-5">
        <div class="spinner-border text-primary" role="status"><span class="visually-hidden">查詢中...</span></div>
        <p class="mt-3 text-muted">同時查詢機票與雪票，請稍候…</p>
      </div>`;
  }

  function renderResults(flights, ski, flightErr, skiErr, backend) {
    const hasFlights = flights.length > 0;
    const hasSki     = ski.length > 0;
    const hasAny     = hasFlights || hasSki;

    const dlBtn = hasAny
      ? `<button id="plan-dl-btn" class="btn btn-success">
           <i class="bi bi-download me-1"></i>下載整合 Excel
         </button>`
      : '';

    // 機票 table rows
    const flightRows = hasFlights ? flights.slice(0, 20).map((r, i) => {
      const stopsBadge = r.stops === 0
        ? '<span class="badge bg-success">直飛</span>'
        : `<span class="badge bg-warning text-dark">${r.stops}&nbsp;轉</span>`;
      return `<tr>
        <td class="fw-semibold">${escHtml(extractAirline(r))}</td>
        <td class="fw-semibold">${fmtTime(r.dep_time)}</td>
        <td>${fmtTime(r.arr_time)}</td>
        <td class="text-muted small">${escHtml(r.duration ?? '—')}</td>
        <td>${stopsBadge}</td>
        <td class="fw-bold text-danger">NT$&nbsp;${Number(r.price ?? 0).toLocaleString()}</td>
      </tr>`;
    }).join('') : '';

    // 雪票 table rows
    const skiRows = hasSki ? ski.map(r => `<tr>
      <td class="fw-semibold">${escHtml(r.resort ?? '')}</td>
      <td><span class="badge region-badge-${escHtml(r.region ?? '')}">${escHtml(r.region ?? '')}</span></td>
      <td class="small">${escHtml(r.ticket_type ?? '')}</td>
      <td class="fw-bold">${escHtml(r.price ?? '')}</td>
      <td>${r.source_url ? `<a href="${escHtml(r.source_url)}" target="_blank" rel="noopener noreferrer" class="btn btn-outline-secondary btn-sm py-0"><i class="bi bi-box-arrow-up-right"></i></a>` : '—'}</td>
    </tr>`).join('') : '';

    const backendBadge = backend === 'SerpAPI'
      ? '<span class="badge bg-success ms-1 fw-normal small">SerpAPI ✓</span>'
      : backend ? `<span class="badge bg-warning text-dark ms-1 fw-normal small">${escHtml(backend)}</span>` : '';

    resultsEl.innerHTML = `
      <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
        <h2 class="h5 fw-bold mb-0">查詢結果</h2>
        ${dlBtn}
      </div>

      <!-- 機票結果 -->
      <div class="card shadow-sm border-0 mb-4">
        <div class="card-header bg-info text-white d-flex justify-content-between align-items-center" style="cursor:pointer" data-bs-toggle="collapse" data-bs-target="#flight-collapse">
          <span><i class="bi bi-airplane me-2"></i>機票結果 ${backendBadge}
            <span class="badge bg-white text-dark ms-2">${flights.length} 筆</span>
          </span>
          <i class="bi bi-chevron-down"></i>
        </div>
        <div id="flight-collapse" class="collapse show">
          <div class="card-body p-0">
            ${flightErr ? `<div class="alert alert-warning m-3">${escHtml(flightErr)}</div>` :
              hasFlights ? `
              <div class="results-table-wrap">
                <table class="table table-hover align-middle mb-0">
                  <thead class="table-dark">
                    <tr><th>航空公司</th><th>出發</th><th>抵達</th><th>飛行時間</th><th>轉機</th><th>票價</th></tr>
                  </thead>
                  <tbody>${flightRows}</tbody>
                </table>
              </div>` :
              '<p class="text-muted p-3 mb-0">無航班結果</p>'}
          </div>
        </div>
      </div>

      <!-- 雪票結果 -->
      <div class="card shadow-sm border-0 mb-4">
        <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center" style="cursor:pointer" data-bs-toggle="collapse" data-bs-target="#ski-collapse">
          <span><i class="bi bi-tag me-2"></i>雪票結果
            <span class="badge bg-white text-dark ms-2">${ski.length} 筆</span>
          </span>
          <i class="bi bi-chevron-down"></i>
        </div>
        <div id="ski-collapse" class="collapse show">
          <div class="card-body p-0">
            ${skiErr ? `<div class="alert alert-warning m-3">${escHtml(skiErr)}</div>` :
              hasSki ? `
              <div class="results-table-wrap">
                <table class="table table-hover table-striped align-middle mb-0">
                  <thead class="table-dark">
                    <tr><th>雪場</th><th>地區</th><th>票種</th><th>票價</th><th>官網</th></tr>
                  </thead>
                  <tbody>${skiRows}</tbody>
                </table>
              </div>` :
              '<p class="text-muted p-3 mb-0">無雪票結果（無設定 ticket_url 的雪場會略過）</p>'}
          </div>
        </div>
      </div>`;

    if (hasAny) {
      document.getElementById('plan-dl-btn')?.addEventListener('click', downloadExcel);
    }
  }

  async function downloadExcel() {
    const btn = document.getElementById('plan-dl-btn');
    if (!btn) return;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>產生中…';
    try {
      const res = await fetch('/api/plan/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ flights: lastFlights, ski: lastSki, meta: lastMeta }),
      });
      if (!res.ok) throw new Error('伺服器錯誤');
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement('a');
      a.href     = url;
      a.download = `snowtrip_${lastMeta.origin}-${lastMeta.destination}_${lastMeta.departure}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert('下載失敗：' + err.message);
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-download me-1"></i>下載整合 Excel';
    }
  }
})();
