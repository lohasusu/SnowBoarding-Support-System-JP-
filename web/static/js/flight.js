(function () {
  'use strict';

  const form      = document.getElementById('flight-form');
  const resultsEl = document.getElementById('flight-results');
  let allData      = [];
  let isRoundtrip  = false;
  let activeAirlines = new Set();
  let searchMeta   = {};

  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // 最小日期：今天
  document.getElementById('departure').min = new Date().toISOString().split('T')[0];
  document.getElementById('departure').addEventListener('change', function () {
    document.getElementById('ret-date').min = this.value;
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const origin    = document.getElementById('origin').value;
    const destEl    = document.getElementById('destination');
    const dest      = destEl.value;
    const destName  = destEl.options[destEl.selectedIndex].dataset.name;
    const departure = document.getElementById('departure').value;
    const retDate   = document.getElementById('ret-date').value;
    const adults    = document.getElementById('adults').value;

    if (!departure) { alert('請輸入出發日期'); return; }

    isRoundtrip  = !!retDate;
    searchMeta   = { origin, destination: dest, dest_name: destName, departure, ret_date: retDate, adults: Number(adults) };
    activeAirlines.clear();
    setLoading();

    const params = new URLSearchParams({ origin, destination: dest, dest_name: destName, departure, adults });
    if (retDate) params.append('ret_date', retDate);

    try {
      const res  = await fetch(`/api/flight/search?${params}`);
      const json = await res.json();
      if (!json.ok) throw new Error(json.error);
      allData = sortFlights(json.data);
      searchMeta._backend = json.backend || '';
      renderFlights();
    } catch (err) {
      setError(err.message);
    }
  });

  function sortFlights(data) {
    return [...data].sort((a, b) => {
      const ta = a.dep_time || '';
      const tb = b.dep_time || '';
      if (ta !== tb) return ta < tb ? -1 : 1;
      return (a.price ?? 0) - (b.price ?? 0);
    });
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
      .filter(Boolean)
      .join(' / ') || '未知';
  }

  function uniqueAirlines(data) {
    const names = new Set();
    data.forEach(r => {
      extractAirline(r).split(' / ').forEach(n => { if (n.trim()) names.add(n.trim()); });
    });
    return [...names].sort();
  }

  function renderFlights() {
    if (!allData.length) {
      resultsEl.innerHTML = `
        <div class="alert alert-warning d-flex align-items-center gap-2" role="alert">
          <i class="bi bi-info-circle-fill flex-shrink-0"></i>
          <div>沒有找到符合條件的航班，請嘗試其他日期或目的地。</div>
        </div>`;
      return;
    }

    const filtered = activeAirlines.size === 0
      ? allData
      : allData.filter(r => {
          const name = extractAirline(r);
          return [...activeAirlines].some(a => name.includes(a));
        });

    const airlines = uniqueAirlines(allData);

    const rows = filtered.map(r => {
      const stopsBadge = r.stops === 0
        ? '<span class="badge bg-success">直飛</span>'
        : `<span class="badge bg-warning text-dark">${r.stops}&nbsp;轉</span>`;
      return `
        <tr>
          <td class="fw-semibold">${escHtml(extractAirline(r))}</td>
          <td class="text-muted small" title="${escHtml(r.flights_str ?? '')}">${escHtml(r.flights_str ?? '')}</td>
          <td class="fw-semibold">${fmtTime(r.dep_time)}</td>
          <td>${fmtTime(r.arr_time)}</td>
          <td class="text-muted small">${escHtml(r.duration ?? '—')}</td>
          <td>${stopsBadge}</td>
          <td class="fw-bold text-danger">NT$&nbsp;${Number(r.price ?? 0).toLocaleString()}</td>
        </tr>`;
    }).join('');

    const airlineBadges = airlines.map(a => {
      const active = activeAirlines.has(a);
      return `<button class="btn btn-sm ${active ? 'btn-info text-white' : 'btn-outline-secondary'} airline-filter-btn"
                      data-airline="${escHtml(a)}">${escHtml(a)}</button>`;
    }).join('');

    const gfUrl = `https://www.google.com/travel/flights?q=flights+from+${searchMeta.origin}+to+${searchMeta.destination}`
      + (searchMeta.departure ? `+on+${searchMeta.departure}` : '');

    const rtNote = isRoundtrip ? `
      <div class="alert alert-info py-2 small mb-3" role="note">
        <i class="bi bi-info-circle me-1"></i>
        票價為<strong>去回程合計</strong>，回程班次詳情請點右上角「Google Flights 驗證」查看
      </div>` : '';

    resultsEl.innerHTML = `
      <div class="d-flex justify-content-between align-items-center mb-2 flex-wrap gap-2">
        <h2 class="h5 mb-0 fw-bold">
          搜尋結果
          <span class="badge bg-info ms-1">${filtered.length} / ${allData.length} 筆</span>
          ${searchMeta._backend === 'SerpAPI'
            ? '<span class="badge bg-success ms-1 fw-normal small">SerpAPI ✓</span>'
            : searchMeta._backend
              ? `<span class="badge bg-warning text-dark ms-1 fw-normal small">${escHtml(searchMeta._backend)}</span>`
              : ''}
        </h2>
        <div class="d-flex gap-2 flex-wrap">
          <a href="${gfUrl}" target="_blank" rel="noopener noreferrer"
             class="btn btn-sm btn-outline-secondary" title="在 Google Flights 驗證資料正確性">
            <i class="bi bi-box-arrow-up-right me-1"></i>Google Flights 驗證
          </a>
          <button id="dl-btn" class="btn btn-sm btn-success">
            <i class="bi bi-download me-1"></i>下載 Excel
          </button>
        </div>
      </div>

      ${rtNote}

      <div class="card border-0 bg-light mb-3 p-3">
        <div class="d-flex align-items-center gap-2 flex-wrap">
          <span class="small fw-semibold text-muted me-1">
            <i class="bi bi-funnel me-1"></i>篩選航空：
          </span>
          <button class="btn btn-sm ${activeAirlines.size === 0 ? 'btn-info text-white' : 'btn-outline-secondary'} airline-filter-btn"
                  data-airline="__all__">全部</button>
          ${airlineBadges}
        </div>
      </div>

      <div class="results-table-wrap">
        <table class="table table-hover align-middle mb-0">
          <thead class="table-dark">
            <tr>
              <th>航空公司 <i class="bi bi-funnel-fill text-info small" title="上方可篩選"></i></th>
              <th>航班號</th>
              <th>出發 <i class="bi bi-sort-up small text-warning" title="已依此排序"></i></th>
              <th>抵達</th>
              <th>飛行時間</th>
              <th>轉機</th>
              <th>票價 <i class="bi bi-sort-up small text-warning" title="同時間依票價排序"></i></th>
            </tr>
          </thead>
          <tbody>${rows || '<tr><td colspan="7" class="text-center text-muted py-3">沒有符合篩選條件的航班</td></tr>'}</tbody>
        </table>
      </div>`;

    document.querySelectorAll('.airline-filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const airline = btn.dataset.airline;
        if (airline === '__all__') {
          activeAirlines.clear();
        } else if (activeAirlines.has(airline)) {
          activeAirlines.delete(airline);
        } else {
          activeAirlines.add(airline);
        }
        renderFlights();
      });
    });

    document.getElementById('dl-btn')?.addEventListener('click', async () => {
      const btn = document.getElementById('dl-btn');
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>產生中…';
      try {
        const res = await fetch('/api/flight/download', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ flights: allData, meta: searchMeta }),
        });
        if (!res.ok) throw new Error('伺服器錯誤');
        const blob = await res.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = `flights_${searchMeta.origin}-${searchMeta.destination}_${searchMeta.departure}.xlsx`;
        a.click();
        URL.revokeObjectURL(url);
      } catch (err) {
        alert('下載失敗：' + err.message);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-download me-1"></i>下載 Excel';
      }
    });
  }

  function setLoading() {
    resultsEl.innerHTML = `
      <div class="text-center py-5">
        <div class="spinner-border text-info" role="status">
          <span class="visually-hidden">搜尋中...</span>
        </div>
        <p class="mt-3 text-muted">正在搜尋最低票價，請稍候…</p>
      </div>`;
  }

  function setError(msg) {
    resultsEl.innerHTML = `
      <div class="alert alert-danger d-flex align-items-center gap-2" role="alert">
        <i class="bi bi-exclamation-triangle-fill flex-shrink-0"></i>
        <div>搜尋失敗：${escHtml(msg)}</div>
      </div>`;
  }
})();
