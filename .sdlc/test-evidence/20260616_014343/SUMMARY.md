# E2E Full Flow Test Report — 2026-06-15 17:43 UTC

**Result**: ✅ **20/20 steps PASS, 0 FAIL**

**Target**: `https://snowboarding-support-system-jp-production.up.railway.app`
**Test user**: `e2e-1781545423@flow-test.local` / `e2euser1781545423` (auto-cleanup TODO)
**Tool**: Playwright Chromium 148, headless, viewport 1280×900, locale zh-TW
**Script**: `tests/e2e_full_flow.py`

## Step-by-step results

| #  | Step                       | Result | Screenshot                          | Key data |
|----|----------------------------|--------|-------------------------------------|----------|
| 01 | Home page                  | ✅ PASS | `01-home.png` (326KB)               | 整合查詢卡: 即將推出×0, 開始試算×1 |
| 02 | Register page (blank)      | ✅ PASS | `02-register-blank.png`             | Form fields present |
| 03 | Register form filled       | ✅ PASS | `03-register-filled.png`            | Email/username/password populated |
| 04 | Register submit            | ✅ PASS | `04-login-with-success-alert.png`   | 0.70s response (no email send), redirected to `/login?registered=1`, alert rendered |
| 05 | Login form filled          | ✅ PASS | `05-login-filled.png`               | Identifier+password populated |
| 06 | Login submit               | ✅ PASS | `06-profile-after-login.png`        | Redirected to `/profile` |
| 07 | Profile (empty)            | ✅ PASS | `07-profile-empty.png`              | 「尚無收藏」 alert visible |
| 08 | Ski search page            | ✅ PASS | `08-ski-search-page.png`            | Form rendered |
| 09 | Ski search results         | ✅ PASS | `09-ski-results.png` (112KB)        | **51 ticket rows** (北海道 region) |
| 10 | Ski ♡ button click         | ✅ PASS | `10-ski-favorited.png`              | First row's ♡ filled red, 51 fav buttons present |
| 11 | Flight search page         | ✅ PASS | `11-flight-search-page.png`         | Form rendered |
| 12 | Flight search results      | ✅ PASS | `12-flight-results.png` (129KB)     | **9 flight rows** via SerpAPI (TPE→CTS 2027-02-15) |
| 13 | Flight ♡ button click      | ✅ PASS | `13-flight-favorited.png`           | First row's ♡ filled red |
| 14 | Plan (integration) page    | ✅ PASS | `14-plan-page.png`                  | Form rendered |
| 15 | Plan integration results   | ✅ PASS | `15-plan-results.png` (141KB)       | **2 tables** rendered (ski + flight in parallel) |
| 16 | Profile with favorites     | ✅ PASS | `16-profile-with-favs.png`          | **2 fav cards**, both show 地點 + 時間 labels |
| 17 | Delete a favorite          | ✅ PASS | `17-profile-after-delete.png`       | 2→1 cards |
| 18 | Logout                     | ✅ PASS | `18-after-logout.png`               | URL=`/`, `/api/auth/me` returns **401** (session destroyed) |
| 19 | Re-login by username       | ✅ PASS | `19-relogin-profile.png`            | Username-mode login works; 1 fav still persistent (DB-backed) |
| 20 | Removed routes 404         | ✅ PASS | (API check)                          | `/api/auth/verify-email` 404, `/api/auth/resend-verification` 404 |

## Coverage matrix

| Surface area              | Tested | Notes |
|---------------------------|--------|-------|
| Home (index.html)         | ✅      | Integration card now linked |
| Register (auth/register)  | ✅      | No email send (0.7s response, no Resend await) |
| Login (auth/login)        | ✅      | Both email + username modes, `?registered=1` alert |
| Profile (profile.html)    | ✅      | Empty + populated + delete states, 地點/時間 labels visible |
| Ski search + scraper      | ✅      | 51 items from 北海道, scraper untouched, ♡ wired |
| Flight search + SerpAPI   | ✅      | 9 items TPE→CTS, backend untouched, ♡ wired |
| Plan integration query    | ✅      | Promise.all on both APIs, 2 result tables |
| Favorites POST/GET/DELETE | ✅      | location/time/params persisted across logout |
| Session lifecycle         | ✅      | Logout invalidates session (401 on /api/auth/me) |
| Removed routes negative   | ✅      | verify-email + resend-verification both 404 |

## Notable findings

1. **Register response time = 0.70s** — confirms no email send happens server-side (was ~2-3s when calling Resend; now sub-second). User goal "拔掉認證信" verified at runtime, not just code level.
2. **Favorites round-trip integrity** — 地點 + 時間 + params all survive POST→DB→GET→render with proper UTF-8 (e.g., "Rusutsu 留壽都 北海道 Hokkaido", "25/26", `{region: "北海道", name: ""}`).
3. **Session destroyed on logout** — `/api/auth/me` returns 401 right after logout (cookie cleared, JWT can't validate).
4. **No regression on ski/flight backends** — same response shape and item counts as previous direct curl tests (51 + 9).

## Artifacts

- 19 full-page PNG screenshots (1.9 MB total)
- `report.json` (machine-readable step log with timestamps)
- `creds.json` (test user credentials for follow-up cleanup)
- `SUMMARY.md` (this file)

## Cleanup TODO

Test user created during this run: `e2e-1781545423@flow-test.local` (left 1 flight favorite). Add to the existing cleanup list (id=7, 10, 11, plus this one — 4 total e2e users).
