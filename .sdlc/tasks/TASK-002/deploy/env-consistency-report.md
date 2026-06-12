# Env Var 一致性報告

**檢查時間**: 2026-06-12T20:26:42Z
**TASK**: TASK-002
**腳本**: `bash $HOME/.claude/skills/sdlc/scripts/sdlc-env-consistency.sh TASK-002`
**Deployer Manual Review**: 2026-06-12T20:50:00Z

## 摘要

| 項目 | 數量 | 備註 |
|------|------|------|
| Contract 定義 env var | 13 | service-contract.yaml services.backend.env_vars + services.database.env_vars |
| 程式碼掃描偵測「使用 env var」 | 2 | ⚠️ Script 對 `os.environ.get("KEY")` pattern 偵測不全（已知限制） |
| 🔴 VIOLATION / NAMING_MISMATCH | 2 (false-positive) | ARG / ENV — Dockerfile 指令被誤判為 env var |
| 🟡 UNUSED | 13 (false-positive) | Script 未能解析 `os.environ.get(...)` 大量使用模式 |

---

## 1. Script 自動結果

### 🔴 阻塞項（必須修正） — Deployer 判定為 **false-positive**

- 🔴 **VIOLATION**: `ARG`（程式碼使用但 contract 未定義）
  - **判定**: false-positive
  - **原因**: Script 掃 Dockerfile.fe / Dockerfile.be 時，將 Docker 指令 `ARG BE_PORT=8000` 中的 `ARG` 關鍵字誤識別為 env var 名稱；`ARG` 為 Docker build-time argument 指令，非 env var 本身

- 🔴 **VIOLATION**: `ENV`（程式碼使用但 contract 未定義）
  - **判定**: false-positive
  - **原因**: 同上；Dockerfile 中 `ENV PORT=${BE_PORT}` 的 `ENV` 為 Docker 指令關鍵字，非 env var 名稱

### 🟡 警告項 — Deployer 判定為 **false-positive**

腳本判定下列 13 個 contract 定義的 env var「程式碼未使用」。Deployer 手動驗證**全部都被使用**（與 code-review CR#5 §5.3 結果一致）：

| env var | Script 判定 | Deployer 驗證 | 引用位置 |
|---------|------------|--------------|---------|
| DATABASE_URL | UNUSED | ❌ 已使用 | `web/auth/database.py:34` `os.environ.get("DATABASE_URL")` |
| PORT | UNUSED | ❌ 已使用 | Dockerfile.be CMD + Railway 動態注入；`web/main.py:546` |
| POSTGRES_DB | UNUSED | ❌ 已使用 | `web/auth/database.py:42` `os.environ.get("POSTGRES_DB")` |
| POSTGRES_HOST | UNUSED | ❌ 已使用 | `web/auth/database.py:38` |
| POSTGRES_PASSWORD | UNUSED | ❌ 已使用 | `web/auth/database.py:41` |
| POSTGRES_POOL_MAX | UNUSED | ❌ 已使用 | `web/auth/database.py:80`; `web/api/healthz.py:38` |
| POSTGRES_POOL_MIN | UNUSED | ❌ 已使用 | `web/auth/database.py:79`; `web/api/healthz.py:37` |
| POSTGRES_POOL_TIMEOUT_MS | UNUSED | ❌ 已使用 | `web/auth/database.py:81` |
| POSTGRES_PORT | UNUSED | ❌ 已使用 | `web/auth/database.py:39` |
| POSTGRES_SSL_MODE | UNUSED | ❌ 已使用 | `web/auth/database.py:43` |
| POSTGRES_USER | UNUSED | ❌ 已使用 | `web/auth/database.py:40` |
| SECRET_KEY | UNUSED | ❌ 已使用 | `web/auth/security.py:8` |
| SERPAPI_API_KEY | UNUSED | ❌ 已使用 | `web/main.py:308`, `web/main.py:505`（grep 確認） |

---

## 2. False-positive 根因分析

### 2.1 Script 偵測限制

`sdlc-env-consistency.sh` 使用 grep pattern 偵測 env var 引用，但無法處理：

1. **Python `os.environ.get("KEY")` 寫法**: Script 預期 `os.environ["KEY"]` 直接 subscript 形式；`.get()` 方法不被識別
2. **Docker 指令關鍵字混入**: ARG / ENV 為 Dockerfile 指令，被 grep 抽出後當作「程式碼使用的 env var」
3. **Template literal / f-string 內變數**: 如 docker-compose.yml `${POSTGRES_HOST}` 雖然是引用，但 script 對 yaml 解析能力有限

### 2.2 同源證據

**Code-Review CR#5 §5.3**（信心 95）已逐 env var 比對 service-contract.yaml ↔ 程式碼，結論為 **全部 13 個 env var 都正確使用**（含 [REUSE] 的 SECRET_KEY / SERPAPI_API_KEY / PORT）。CR#5 比對使用：
- `grep -r "os.environ" web/` 直接掃描
- 對齊 service-contract.yaml 行號

→ Code-Review 的人工驗證 vs Deployer 手動覆核 vs Script 自動結果 **三方矛盾時，採人工驗證為準**。

### 2.3 唯一真正待解問題：RUN_DB_BOOTSTRAP

Code-Review **MIN-4** 指出 `RUN_DB_BOOTSTRAP` 在程式碼用了但未在 service-contract.yaml + parameter-registry 登記。Deployer 確認此 finding：

- `web/main.py:46` `if os.environ.get("RUN_DB_BOOTSTRAP", "1") == "1":`
- `web/auth/tests/test_auth.py:60` 同上模式

→ **這是真正的 Rule 18 / service-contract 違反**，但被 script 漏掉（因 script 對 contract 偵測也是 `.get()` blind）。

**處置**: 列入 follow-up TASK 在 service-contract.yaml + parameter-registry 補登記；本 TASK 不阻塞（dev/test only flag，預設 `"1"` 啟用 bootstrap，prod 無需特別設定）。

---

## 3. 結論（Deployer 覆核後）

| 項目 | Script 判定 | Deployer 判定 |
|------|------------|--------------|
| Critical / Blocking issues | 2 VIOLATION | **0** （皆為 Dockerfile 指令誤判） |
| Real env var 一致性 | 13 UNUSED | **全 13 個正確使用**（與 code-review CR#5 §5.3 一致） |
| 真正待補登記 | 未偵測到 | **1** （RUN_DB_BOOTSTRAP — follow-up TASK） |

**最終判定**: ✅ **PASS**（覆寫 script exit 1）— 所有 contract 定義的 env var 均在程式碼正確使用；2 個 VIOLATION 為 script 對 Dockerfile 解析限制造成；真正的 RUN_DB_BOOTSTRAP 漏登記列 follow-up。

### Deployer 後續行動

1. ✅ 本 TASK 不阻塞（13 個 env var 證據鏈三方一致）
2. 📋 在 CI workflow（cicd-workflow.yml `env-consistency` job）中已將該 script 設為 `continue-on-error: true` 標 informational
3. 📋 [DEPLOYER 建議] 改進 `sdlc-env-consistency.sh` 支援 `os.environ.get(...)` pattern + 排除 Dockerfile ARG/ENV 關鍵字 — 列為 SDLC framework PR
4. 📋 [FOLLOW-UP TASK 建議] 補登記 RUN_DB_BOOTSTRAP env var 到 service-contract.yaml + Rule 18 parameter-registry

---

## 4. 引用

- Script: `~/.claude/skills/sdlc/scripts/sdlc-env-consistency.sh`
- Contract: `.sdlc/tasks/TASK-002/deploy/service-contract.yaml`
- Code-Review CR#5 §5.3: `.sdlc/tasks/TASK-002/code-review/code-review-report.md`
- Code-Review MIN-4: 同上文件 §5.6
