(function () {
  'use strict';

  function escHtml(str) {
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  // ── 登入表單 ──────────────────────────────────────────────────────────────
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      // 支援 Email 或 username — 都塞進 email 欄送出（後端會判斷）
      const idEl     = document.getElementById('login-identifier') || document.getElementById('login-email');
      const email    = idEl.value.trim();
      const password = document.getElementById('login-password').value;
      const errEl    = document.getElementById('login-error');
      errEl.classList.add('d-none');
      loginForm.querySelector('[type=submit]').disabled = true;

      try {
        const res  = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        });
        const json = await res.json();
        if (!res.ok) {
          // 403 = 未驗證 email，顯示「重寄驗證信」按鈕
          if (res.status === 403) {
            const resendArea = document.getElementById('resend-area');
            if (resendArea) resendArea.classList.remove('d-none');
          }
          throw new Error(json.detail || '登入失敗');
        }
        location.href = '/profile';
      } catch (err) {
        errEl.textContent = err.message;
        errEl.classList.remove('d-none');
      } finally {
        loginForm.querySelector('[type=submit]').disabled = false;
      }
    });
  }

  // ── 註冊表單 ──────────────────────────────────────────────────────────────
  const registerForm = document.getElementById('register-form');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email    = document.getElementById('reg-email').value.trim();
      const username = document.getElementById('reg-username').value.trim();
      const password = document.getElementById('reg-password').value;
      const errEl    = document.getElementById('register-error');
      errEl.classList.add('d-none');
      registerForm.querySelector('[type=submit]').disabled = true;

      try {
        const res  = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, username, password }),
        });
        const json = await res.json();
        if (!res.ok) throw new Error(json.detail || '註冊失敗');

        // 註冊成功 → 不要自動跳登入頁。
        // 顯示「請收信並點驗證連結」面板；點信中連結後 verify-email 會 302 到 /login?verified=1
        const checkPanel = document.getElementById('register-check-email');
        const emailAddr  = document.getElementById('check-email-addr');
        if (checkPanel && emailAddr) {
          emailAddr.textContent = email;
          registerForm.classList.add('d-none');
          document.getElementById('register-divider')?.classList.add('d-none');
          document.getElementById('register-login-link')?.classList.add('d-none');
          checkPanel.classList.remove('d-none');
          const title = document.getElementById('register-title');
          if (title) title.textContent = '註冊成功';
        }
      } catch (err) {
        errEl.textContent = err.message;
        errEl.classList.remove('d-none');
        registerForm.querySelector('[type=submit]').disabled = false;
      }
    });
  }

  // ── 收藏按鈕（ski/flight 結果頁使用）────────────────────────────────────
  // 使用方式：dispatchEvent(new CustomEvent('add-favorite', { detail: { type, data, label } }))
  window.addFavorite = async function (type, data, label) {
    try {
      const res  = await fetch('/api/favorites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type, data, label }),
      });
      const json = await res.json();
      if (res.status === 401) {
        if (confirm('請先登入才能收藏。前往登入頁？')) location.href = '/login';
        return;
      }
      if (!res.ok) throw new Error(json.detail || '收藏失敗');
      alert('已加入收藏！');
    } catch (err) {
      alert('收藏失敗：' + err.message);
    }
  };
})();
