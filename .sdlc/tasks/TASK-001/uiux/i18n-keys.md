---
document_id: "I18N-TASK-001-v1.0"
title: "i18n Key 建議清單 — snowboarding_support brownfield"
version: "1.0"
date: "2026-06-15"
author: "UIUX"
status: "Draft"
task_id: "TASK-001"
phase: "uiux"
mode: "brownfield-document"
source_documents:
  - "WF-TASK-001-v1.0"
  - "COMP-TASK-001-v1.0"
  - "web/templates/*.html"
  - "web/static/js/*.js"
change_history:
  - version: "1.0"
    date: "2026-06-15"
    changes: "初始版本 — 列出所有硬編碼 UI 文字 → 建議 i18n key（brownfield only — 不強制重構）"
    author: "UIUX"
---

# i18n Key 建議清單

> **狀態**: 建議（**brownfield 不強制重構**）
> **理由**: BA NFR-015 明示「zh-TW 為唯一支援語系」+ i18n-conventions.md v1.1 §1 brownfield 階段不啟用 i18n key 機制
> **未來啟用時機**: Vue 重構階段（config.json frontend.framework=vue）才需要正式 i18n key
> **本檔目的**: 預先盤點所有 UI 文字位置，方便未來重構時批次建表

---

## 1. 命名規範（建議）

```
{ns}.{domain}.{name}
```

- **ns**: common / nav / page / form / error / message / button
- **domain**: 業務領域（auth / ski / flight / plan / favorite / footer）
- **name**: 具體文字 slug

範例: `nav.brand.title`, `page.ski.title`, `form.login.identifier-label`, `error.auth.invalid-credentials`

---

## 2. 全域共用文字

| Key 建議 | 中文 | 來源 |
|---------|------|------|
| `nav.brand.title` | SnowTrip Japan | `base.html:83` |
| `nav.item.ski` | 雪票查詢 | `base.html:97` |
| `nav.item.flight` | 機票查詢 | `base.html:104` |
| `nav.item.plan` | 整合查詢 | `base.html:111` |
| `nav.user.login` | 登入 | `base.html:119` |
| `nav.accessibility.toggle` | 展開導覽選單 | `base.html:88` |
| `nav.accessibility.brand` | SnowTrip Japan 首頁 | `base.html:82` |
| `accessibility.skip-link` | 跳到主要內容 | `base.html:76` |
| `footer.brand.tagline` | 一站式日本滑雪行程規劃工具... | `base.html:142` |
| `footer.section.features` | 功能 | `base.html:147` |
| `footer.section.regions` | 熱門地區 | `base.html:153` |
| `footer.copyright` | © 2026 SnowTrip Japan．票價資料僅供參考... | `base.html:165` |
| `common.breadcrumb.home` | 首頁 | `ski.html:37`, `flight.html:37`, `plan.html:34` |

---

## 3. PAGE-001 首頁

| Key 建議 | 中文 | 來源 |
|---------|------|------|
| `page.home.title` | SnowTrip Japan — 日本滑雪行程一站規劃 | `index.html:3` |
| `page.home.hero.title` | SnowTrip Japan | `index.html:27` |
| `page.home.hero.subtitle` | 一站式日本滑雪行程規劃 | `index.html:30` |
| `page.home.hero.tagline` | 查早鳥雪票 ・ 找最便宜機票 | `index.html:31` |
| `page.home.hero.cta-ski` | 查雪票 | `index.html:35` |
| `page.home.hero.cta-flight` | 找機票 | `index.html:38` |
| `page.home.stats.snow-fields` | 日本雪場 | `index.html:50` |
| `page.home.stats.regions` | 主要地區 | `index.html:54` |
| `page.home.stats.update` | 資料更新 | `index.html:58` |
| `page.home.features.title` | 功能一覽 | `index.html:66` |
| `page.home.features.ski.title` | 雪票查詢 | `index.html:77` |
| `page.home.features.ski.desc` | 即時查詢 40+ 日本雪場早鳥票、一般票價格... | `index.html:79` |
| `page.home.features.ski.cta` | 開始查詢 | `index.html:81` |
| `page.home.features.flight.title` | 機票查詢 | `index.html:94` |
| `page.home.features.flight.desc` | 搜尋台北桃園、松山、高雄、台中出發... | `index.html:96` |
| `page.home.features.flight.cta` | 搜尋機票 | `index.html:98` |
| `page.home.features.plan.title` | 整合查詢 | `index.html:112` |
| `page.home.features.plan.badge-soon` | 即將推出 | `index.html:113` |
| `page.home.features.plan.desc` | 輸入日期 + 預算 + 地區... | `index.html:115` |
| `page.home.features.plan.cta-disabled` | 敬請期待 | `index.html:118` |
| `page.home.steps.title` | 如何使用 | `index.html:129` |
| `page.home.regions.title` | 熱門地區 | `index.html:152` |

---

## 4. PAGE-002 雪票查詢

| Key 建議 | 中文 | 來源 |
|---------|------|------|
| `page.ski.title` | 雪票查詢 — SnowTrip Japan | `ski.html:3` |
| `page.ski.heading` | 雪票查詢 | `ski.html:42` |
| `page.ski.description` | 查詢日本各雪場早鳥票、一般票價格（資料每日更新）| `ski.html:43` |
| `form.ski.search-heading` | 搜尋條件 | `ski.html:49` |
| `form.ski.region-label` | 地區 | `ski.html:54` |
| `form.ski.region.all` | 全部地區 | `ski.html:56` |
| `form.ski.name-label` | 雪場名稱 | `ski.html:66` |
| `form.ski.name-optional` | （選填）| `ski.html:67` |
| `form.ski.name-placeholder` | 例：Furano、白馬 | `ski.html:69` |
| `form.ski.submit` | 查詢 | `ski.html:74` |
| `form.ski.download` | Excel | `ski.html:78` |
| `form.ski.download-tooltip` | 查詢後可下載 Excel | `ski.html:76` |
| `message.ski.empty-prompt` | 請選擇地區或輸入雪場名稱後按下查詢 | `ski.html:91` |
| `message.ski.loading` | 正在連線抓取票價，請稍候… | `ski.js:129` |
| `message.ski.querying-sr` | 查詢中... | `ski.js:127` |
| `message.ski.results-heading` | 查詢結果 | `ski.js:36` |
| `message.ski.results-counter` | {n} 筆 | `ski.js:82` |
| `message.ski.scan-progress` | 已掃描 {done} / {total} 個雪場 | `ski.js:85` |
| `table.ski.header.resort` | 雪場 | `ski.js:44` |
| `table.ski.header.region` | 地區 | `ski.js:45` |
| `table.ski.header.ticket-jp` | 票種（日文）| `ski.js:46` |
| `table.ski.header.ticket-zh` | 票種（中文）| `ski.js:47` |
| `table.ski.header.price` | 票價 | `ski.js:48` |
| `table.ski.header.season` | 雪季 | `ski.js:49` |
| `table.ski.header.url` | 官網 | `ski.js:50` |
| `error.ski.query-failed` | 查詢失敗：{msg} | `ski.js:93` |
| `error.ski.no-result` | 沒有找到符合條件的資料，請嘗試其他地區或名稱。| `ski.js:101` |
| `error.ski.connection-lost` | 連線中斷，請重試 | `ski.js:161, 171` |

---

## 5. PAGE-003 機票查詢

| Key 建議 | 中文 | 來源 |
|---------|------|------|
| `page.flight.title` | 機票查詢 — SnowTrip Japan | `flight.html:3` |
| `page.flight.heading` | 機票查詢 | `flight.html:42` |
| `page.flight.description` | 搜尋台灣出發、前往日本滑雪地區的最低票價 | `flight.html:43` |
| `form.flight.origin-label` | 出發機場 | `flight.html:55` |
| `form.flight.destination-label` | 目的地 | `flight.html:65` |
| `form.flight.departure-label` | 出發日期 | `flight.html:78` |
| `form.flight.return-label` | 回程 | `flight.html:85` |
| `form.flight.adults-label` | 人數 | `flight.html:91` |
| `form.flight.adults-aria` | 成人人數 | `flight.html:93` |
| `form.flight.submit` | 搜尋 | `flight.html:99` |
| `form.flight.notice` | 機票資料來自 Google Flights，價格為即時查詢，僅供參考。| `flight.html:107` |
| `message.flight.empty-prompt` | 請輸入出發日期後按下搜尋 | `flight.html:118` |
| `message.flight.loading` | 正在搜尋最低票價，請稍候… | `flight.js:239` |
| `message.flight.no-result` | 沒有找到符合條件的航班，請嘗試其他日期或目的地。| `flight.js:95` |
| `message.flight.results-heading` | 搜尋結果 | `flight.js:143` |
| `message.flight.results-counter` | {filtered} / {total} 筆 | `flight.js:144` |
| `message.flight.roundtrip-notice` | 票價為去回程合計，回程班次詳情請點右上角「Google Flights 驗證」查看 | `flight.js:136-138` |
| `message.flight.filter-label` | 篩選航空：| `flight.js:167` |
| `message.flight.filter-all` | 全部 | `flight.js:170` |
| `message.flight.no-filtered-result` | 沒有符合篩選條件的航班 | `flight.js:188` |
| `button.flight.gf-verify` | Google Flights 驗證 | `flight.js:154` |
| `button.flight.gf-verify-tooltip` | 在 Google Flights 驗證資料正確性 | `flight.js:153` |
| `button.flight.download` | 下載 Excel | `flight.js:157` |
| `button.flight.downloading` | 產生中… | `flight.js:209` |
| `table.flight.header.airline` | 航空公司 | `flight.js:179` |
| `table.flight.header.flight-no` | 航班號 | `flight.js:180` |
| `table.flight.header.departure` | 出發 | `flight.js:181` |
| `table.flight.header.arrival` | 抵達 | `flight.js:182` |
| `table.flight.header.duration` | 飛行時間 | `flight.js:183` |
| `table.flight.header.stops` | 轉機 | `flight.js:184` |
| `table.flight.header.price` | 票價 | `flight.js:185` |
| `badge.flight.direct` | 直飛 | `flight.js:111` |
| `badge.flight.transfer` | {n} 轉 | `flight.js:112` |
| `error.flight.missing-departure` | 請輸入出發日期 | `flight.js:35` |
| `error.flight.search-failed` | 搜尋失敗：{msg} | `flight.js:247` |
| `error.flight.download-failed` | 下載失敗：{msg} | `flight.js:225` |
| `error.flight.server-error` | 伺服器錯誤 | `flight.js:216` |

---

## 6. PAGE-004 整合查詢

| Key 建議 | 中文 | 來源 |
|---------|------|------|
| `page.plan.title` | 整合查詢 — SnowTrip Japan | `plan.html:2` |
| `page.plan.heading` | 整合查詢 | `plan.html:39` |
| `page.plan.description` | 輸入日期與地區，一次查機票 + 雪票 | `plan.html:40` |
| `form.plan.region-label` | 雪場地區 | `plan.html:70` |
| `message.plan.empty-prompt` | 請填寫搜尋條件後按下查詢 | `plan.html:109` |
| `message.plan.loading` | 同時查詢機票與雪票，請稍候… | `plan.js:95` |
| `section.plan.flight-result` | 機票結果 | `plan.js:147` |
| `section.plan.ski-result` | 雪票結果 | `plan.js:172` |
| `message.plan.results-heading` | 查詢結果 | `plan.js:140` |
| `button.plan.download` | 下載整合 Excel | `plan.js:106` |
| `message.plan.no-flight` | 無航班結果 | `plan.js:164` |
| `message.plan.no-ski` | 無雪票結果（無設定 ticket_url 的雪場會略過）| `plan.js:189` |

---

## 7. PAGE-005 個人 / 收藏

| Key 建議 | 中文 | 來源 |
|---------|------|------|
| `page.profile.title` | 我的帳號 — SnowTrip Japan | `profile.html:2` |
| `page.profile.heading` | 我的帳號 | `profile.html:7` |
| `page.profile.welcome` | 歡迎，{username}（{email}）| `profile.html:8` |
| `button.profile.logout` | 登出 | `profile.html:13` |
| `section.profile.favorites` | 收藏清單 | `profile.html:16` |
| `message.profile.no-favorites` | 尚無收藏。在雪票或機票查詢結果中按下 ♡ 即可收藏。| `profile.html:19` |
| `badge.favorite.ski` | ⛷ 雪票 | `profile.html:29` |
| `badge.favorite.flight` | ✈ 機票 | `profile.html:29` |
| `label.favorite.unnamed` | 未命名 | `profile.html:31` |
| `confirm.favorite.delete` | 確定刪除此收藏？ | `profile.html:62` |

---

## 8. PAGE-006 登入

| Key 建議 | 中文 | 來源 |
|---------|------|------|
| `page.login.title` | 登入 — SnowTrip Japan | `login.html:2` |
| `page.login.heading` | 登入 | `login.html:14` |
| `button.login.google` | 使用 Google 帳號登入 | `login.html:29` |
| `divider.login.or` | 或使用帳號登入 | `login.html:33` |
| `form.login.identifier-label` | Email 或使用者名稱 | `login.html:38` |
| `form.login.identifier-placeholder` | 輸入 Email 或使用者名稱 | `login.html:39` |
| `form.login.password-label` | 密碼 | `login.html:42` |
| `form.login.submit` | 登入 | `login.html:50` |
| `form.login.register-link` | 還沒有帳號？立即註冊 | `login.html:54` |
| `button.login.resend` | 重寄驗證信 | `login.html:48` |
| `button.login.resend.sending` | 寄送中... | `login.html:88` |
| `message.login.verified` | ✅ Email 驗證成功！請登入您的帳號。 | `login.html:67` |
| `message.login.invalid-token` | ❌ 驗證連結已失效或已使用，請重新寄送驗證信。| `login.html:69` |
| `message.login.token-expired` | ⏰ 驗證連結已過期（24 小時），請重新寄送驗證信。| `login.html:71` |
| `message.login.unverified` | 📧 請先驗證您的 Email 後再登入。| `login.html:73` |
| `message.login.resend-ok` | 驗證信已寄出 | `login.html:97` |
| `message.login.resend-fail` | 寄送失敗 | `login.html:97` |
| `error.login.identifier-not-email` | 請在上方輸入您的 Email（重寄驗證信需要 Email，不是使用者名稱）| `login.html:84` |
| `error.login.send-failed` | 寄送失敗：{msg} | `login.html:101` |
| `error.login.default` | 登入失敗 | `auth.js:34` |

---

## 9. PAGE-007 註冊

| Key 建議 | 中文 | 來源 |
|---------|------|------|
| `page.register.title` | 註冊 — SnowTrip Japan | `register.html:2` |
| `page.register.heading` | 建立帳號 | `register.html:14` |
| `form.register.email-label` | Email | `register.html:18` |
| `form.register.username-label` | 用戶名稱 | `register.html:22` |
| `form.register.password-label` | 密碼（至少 8 字元）| `register.html:26` |
| `form.register.submit` | 建立帳號 | `register.html:30` |
| `form.register.login-link` | 已有帳號？立即登入 | `register.html:53` |
| `page.register.success-heading` | 註冊成功 | `auth.js:78` |
| `section.register.check-email-heading` | 驗證信已寄出 | `register.html:37` |
| `section.register.check-email-sent-to` | 已寄驗證信到：| `register.html:40` |
| `section.register.check-email-instruction` | 請至信箱點擊「驗證我的帳號」按鈕，完成後系統會自動帶你回到登入頁。 | `register.html:41` |
| `section.register.check-email-tip-expiry` | 連結有效期 **24 小時** | `register.html:44` |
| `section.register.check-email-tip-spam` | 沒收到？檢查垃圾信件夾、或到登入頁用「重寄驗證信」按鈕 | `register.html:45` |
| `section.register.check-email-tip-username` | 已驗證後可以用 Email 或使用者名稱登入 | `register.html:46` |
| `button.register.back-to-login` | 回登入頁 | `register.html:48` |
| `error.register.default` | 註冊失敗 | `auth.js:65` |
| `error.favorite.add-failed` | 收藏失敗：{msg} | `auth.js:105` |
| `confirm.favorite.login-required` | 請先登入才能收藏。前往登入頁？| `auth.js:99` |
| `message.favorite.added` | 已加入收藏！| `auth.js:103` |

---

## 10. 後端錯誤訊息（後端 HTTPException detail — 透過 API 傳入前端）

> 後端訊息也建議納入 i18n 體系，但目前硬編碼於 Python `detail="..."`。

| Key 建議 | 中文（後端原文）| 來源 |
|---------|----------------|------|
| `api.error.auth.password-too-short` | 密碼至少 8 個字元 | `auth_router.py:87` |
| `api.error.auth.invalid-email` | Email 格式不正確 | `auth_router.py:89` |
| `api.error.auth.duplicate` | Email 或用戶名稱已被使用 | `auth_router.py:106-107` |
| `api.error.auth.register-failed` | 註冊失敗 | `auth_router.py:?` |
| `api.error.auth.invalid-credentials` | Email 或密碼錯誤 | `auth_router.py:?` |
| `api.error.auth.unverified` | 請先驗證您的 Email 後再登入... | `auth_router.py:127` |
| `api.error.auth.no-such-email` | 找不到此 Email 的帳號 | `auth_router.py:?` |
| `api.error.auth.already-verified` | 此帳號已完成驗證 | `auth_router.py:181` |
| `api.error.auth.resent-ok` | 驗證信已重新寄出 | `auth_router.py:?` |
| `api.error.auth.send-failed` | 寄信失敗，請稍後再試 | `auth_router.py:?` |
| `api.error.fav.invalid-type` | type 必須是 ski 或 flight | `auth_router.py:235` |
| `api.error.oauth.not-configured` | Google 登入尚未設定，請聯繫管理員 | `oauth_router.py:?` |
| `api.error.ski.locked` | 查詢進行中，請稍後再試 | `main.py:130` |
| `api.error.ski.timeout` | 查詢逾時（45 秒），請縮小範圍後重試 | `main.py:?` |
| `api.error.flight.missing-departure` | 請輸入出發日期 | `main.py:?` |

---

## 11. 統計

- **總 key 數**: ~140 個 UI 文字 key
- **可重用 key**: ~10 個（如 `common.breadcrumb.home`, `nav.brand.title`, 共用 alert 等）
- **頁面特定 key**: ~110 個
- **後端錯誤 key**: ~20 個（前後端共享）

---

## 12. 啟用建議（後續 TASK 規劃）

1. **不在 TASK-001 內啟用** — brownfield 階段保持現狀
2. **Vue 重構 TASK 時啟用**：
   - 引入 vue-i18n
   - 建立 `src/locales/zh-TW.json` 含所有 key
   - 後端 `detail` 改為英文錯誤碼（如 `ERR-AUTH-001`），前端負責本地化
3. **若未來加日文 / 英文版**: 預先準備 `ja-JP.json` / `en-US.json`

---

## 13. 自我驗證

- [x] 所有 templates 硬編碼文字已盤點
- [x] 所有 JS 動態文字已盤點
- [x] 後端 HTTPException 訊息已盤點
- [x] Key 命名遵循 `{ns}.{domain}.{name}` 規範
- [x] 標明來源 file:line
- [x] 標明「brownfield 不強制重構」
