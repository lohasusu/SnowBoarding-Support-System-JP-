# CLAUDE.md — SnowTrip Japan 開發守則

> Claude Code 在每次對話中自動讀取本文件。

## 每次對話開始必做

1. 讀取 `DESIGN.md`（位於 `D:\SideProject\DESIGN.md`）
2. 了解目前進度後再開始任何修改

## 每次程式碼或邏輯修改後必做

**每次修改完任何程式碼，在同次對話結束前必須更新 `D:\SideProject\DESIGN.md`：**

| 修改類型 | 必須更新的 DESIGN.md 章節 |
|---------|--------------------------|
| 新增路由/API | 5-2 路由表 |
| 新增檔案 | 二、目錄結構 |
| 功能狀態變更 | 七、開發優先順序 |
| 新增已知問題 | 八、已知問題與限制 |
| 任何修改 | 九、下次對話從這裡開始（更新待辦）|
| 任何修改 | 文件末尾最後更新日期 |

**違反此規則等於讓文件與程式碼脫節，後續維護成本倍增。**

## 專案關鍵路徑

| 項目 | 路徑 |
|------|------|
| 設計文件 | `D:\SideProject\DESIGN.md` |
| Git Repo | `D:\SideProject\snowboarding_support\` |
| 生產 API | `web/main.py`（FastAPI + uvicorn）|
| 雪票爬蟲 | `http_scraper.py`（httpx + BS4，無 Playwright）|
| 機票後端 | `flight_search/backends/` |
| 靜態 JS | `web/static/js/`（ski.js / flight.js / plan.js / auth.js）|
| 資料庫 | `web/data/snowtrip.db`（SQLite）|
| 部署 | Railway（`uvicorn web.main:app --host 0.0.0.0 --port $PORT`）|

## 不可破壞的規則

- Railway 環境**不能用 Playwright**（改用 http_scraper.py）
- `/api/ski/search`（批次 JSON）和 `/api/ski/stream`（SSE）**兩個端點都要保留**
- SQLite DB 路徑固定為 `web/data/snowtrip.db`
- JS 邏輯放在 `web/static/js/`，模板不寫 inline script
- 新增功能後必須在 main.py 以 `include_router` 掛載對應 router

## Railway 部署注意事項

- 生產 URL：`https://snowboarding-support-system-jp-production.up.railway.app`
- 啟動指令：`uvicorn web.main:app --host 0.0.0.0 --port $PORT`
- 環境變數：`SERPAPI_API_KEY`（機票）、`SECRET_KEY`（JWT）
- SQLite DB 在 Railway 重啟後**資料會消失**（ephemeral storage）
