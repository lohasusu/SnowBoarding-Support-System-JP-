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

<!-- SDLC-WORKFLOW-START -->
# SDLC Workflow

本專案使用 PM 中心制 SDLC 工作流，所有開發流程由 PM 角色統一派發和管理。

## 狀態檔案
- 專案設定: `.sdlc/config.json`
- 任務狀態: `.sdlc/state.json`
- 任務產出: `.sdlc/tasks/{TASK-ID}/{phase}/`
- 共享層: `.sdlc/shared/` (跨 TASK 一致性索引)
- 規範層: `.sdlc/conventions/` (api/db/code/i18n/branch — 已鎖定)
- 多環境: `.sdlc/environments.json`

## 可用命令
| 命令 | 用途 |
|------|------|
| `/sdlc:start <需求>` | 開始新任務（PM 建立 + BA 需求分析） |
| `/sdlc:next` | 通過當前階段，進入下一階段 |
| `/sdlc:revise <意見>` | 退回修訂（同階段） |
| `/sdlc:rollback-phase <階段>` | 跨階段回退 |
| `/sdlc:status` | 查看專案狀態 |
| `/sdlc:export` | 匯出正式報告 |
| `/sdlc:resume` | 恢復中斷的任務 |

## 專案配置
- **技術棧**: Vue + Vite (前端，未來重構) / FastAPI Python (後端) / PostgreSQL (資料庫，現為 SQLite 待轉換)
- **開發模式**: SDD + BDD + TDD
- **測試頻率**: strict（每階段獨立測試）
- **Git 管理**: docs-only（只 commit .sdlc/ 規格，程式碼分支自管）
- **Registry**: ghcr.io（Buildx: linux/amd64 + linux/arm64）

## 核心規則
1. **反腦補**: 嚴禁自行補充使用者未提及的內容，額外建議必須標記 `[XX建議]`
2. **來源引用**: 每個規格項目必須追溯到需求 ID 或使用者原文
3. **文件先行**: 每階段先產出文件，通過審核才進下一階段
4. **自我驗證**: 每個角色交付前 20 項檢查，≥ 90 分才通過
5. **Conventions 已鎖定**: api/db/code/i18n/branch 5 個 conventions 已 lock，變更走 RFC

## 角色流程
```
BA(需求) → SA(架構) → UIUX(設計) → SD(規格) → FE+BE(開發) → Testing(驗證) → Deploy(部署)
```
每個階段之間可能插入 Testing 驗證（依 testMode=strict 設定，每階段都跑）。

## 已知缺口（init 時記錄）
- Pencil MCP **尚未安裝** — UIUX 階段前必須安裝
- Context7/Chrome/Notion MCP 尚未安裝（非必要，視 SD/FE/Tester 階段需要）
<!-- SDLC-WORKFLOW-END -->
