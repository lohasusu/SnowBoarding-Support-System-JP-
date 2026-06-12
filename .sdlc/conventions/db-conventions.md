---
document_id: "DBCON-CONVENTIONS-v1.1"
title: "資料庫慣例規範"
version: "1.1"
date: "2026-06-03"
author: "PM"
status: "Living Document (Layer 2 conventions/)"
phase: "conventions"
locked_at: "2026-06-03T09:30:00Z"
change_history:
  - version: "1.0"
    date: "2026-06-03"
    changes: "init: 從模板 cp + lock"
    author: "PM"
  - version: "1.1"
    date: "2026-06-03"
    changes: "init customization pass — 無 module 前綴 / PK=BIGINT (Postgres) / Charset=UTF8 / favorites ON DELETE CASCADE / 加入 brownfield SQLite 過渡規則"
    author: "PM"
---

# 資料庫慣例規範（Layer 2 / conventions）

> **用途**: 跨 TASK 統一 DB schema 風格 — 表名、欄位、索引、外鍵、migration。
>
> **生效時機**: 一旦 `/sdlc:init` 鎖定（`locked_at` 欄位寫入），所有 SD 階段必須遵守。修改需要走 RFC 流程（見 §7）。
>
> **角色存取**: SD 唯讀（設計 db-schema.md 時遵循）/ BE 唯讀（migration 實作時遵循）。

---

## 1. 表名規範

| 規則 | 範例 | 說明 |
|------|------|------|
| `snake_case` 複數 | `users`, `order_items` | 不用 `User` / `userTable` / `tbl_users` |
| 不加技術前綴 | `users` | 不用 `t_users` `tbl_users` |
| 連結表用 `_` 串接 | `user_roles`, `order_payment_methods` | 兩個實體中介 |
| TASK 範圍前綴 | **不使用** | 單一領域應用，表名扁平（`users`, `favorites`, `email_verification_tokens`），未來若拆 microservices 再評估 |

## 2. 欄位命名規範

| 類型 | 命名 | 範例 |
|------|------|------|
| 主鍵 | `id` | **Postgres 目標**: `BIGINT GENERATED ALWAYS AS IDENTITY` / **SQLite 現況**: `INTEGER PRIMARY KEY AUTOINCREMENT`（brownfield grandfather） |
| 外鍵 | `{ref_table_singular}_id` | `user_id`, `order_id` |
| 時間戳 | `created_at` / `updated_at` / `deleted_at` | snake_case，DATETIME / TIMESTAMP |
| 布林 | `is_xxx` / `has_xxx` / `can_xxx` | `is_active`, `has_premium` |
| 計數 | `xxx_count` | `comment_count`, `view_count` |
| 列舉/狀態 | `xxx_status` / `xxx_type` | `order_status` ENUM('pending','paid','...') |

**禁止**: camelCase / PascalCase 欄位名 / 縮寫不一致（`usr` vs `user`）

## 3. 索引命名

| 類型 | 前綴 | 範例 |
|------|------|------|
| 一般索引 | `idx_` | `idx_users_email` (single col) / `idx_orders_user_status` (composite) |
| 唯一索引 | `uniq_` | `uniq_users_email` |
| 外鍵索引 | `fk_idx_` | `fk_idx_orders_user_id` |
| 全文索引 | `ft_idx_` | `ft_idx_articles_content` |

## 4. 外鍵約束

```sql
ALTER TABLE orders ADD CONSTRAINT fk_orders_user_id_users
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE RESTRICT  -- 預設保護資料
    ON UPDATE CASCADE;
```

- 外鍵命名: `fk_{table}_{column}_{ref_table}`
- **ON DELETE 預設 RESTRICT**（保護資料）
- **CASCADE 例外白名單**（必須明確列出原因）:
  - `favorites.user_id → users.id`: 用戶刪除即收藏全失 — 合理（既有實作 `web/auth/database.py:34`）
  - `email_verification_tokens.user_id → users.id`: 用戶刪除即驗證 token 失效 — 合理（既有實作 `web/auth/database.py:42`）
  - 任何新增 CASCADE 需 SD 在 db-schema.md 標註理由
- **ON UPDATE 通常 CASCADE**

## 5. Migration 規範

### 5.1 檔名格式
```
{YYYYMMDD_HHMMSS}_{verb}_{noun}.sql
範例: 20260105_140530_create_users_table.sql
範例: 20260108_092045_add_email_index_to_users.sql
```

### 5.2 必須可逆（reversible）
每個 migration 必須有對應的 down 操作：
- 框架方式（Flyway/Liquibase/Knex/Alembic）→ 寫好 down/rollback
- 純 SQL → 同檔案內附 `-- DOWN` 註解區塊或對應 `*_down.sql`

### 5.3 三段式刪欄協議（避免破壞線上版本）
**禁止**單次 migration 直接 DROP COLUMN。須走三步：
1. **Expand**: 新欄位先 nullable 加上 + backfill
2. **Migrate code**: 應用切換到讀寫新欄位
3. **Contract**: 確認無 reads/writes 後才 DROP 舊欄位

### 5.4 大表索引

PostgreSQL: `CREATE INDEX CONCURRENTLY ...`
MySQL: `ALGORITHM=INPLACE, LOCK=NONE`（依版本）

## 6. 字串編碼 / 校對

| 設定 | 值 | 說明 |
|------|------|------|
| Charset | **`UTF8`** (Postgres 目標) | SQLite 現況 = UTF-8（內建）|
| Collation | **預設 (`default`)** — 不指定 | 目前無 case-insensitive search 需求；email 唯一性檢查在應用層用 `.lower()` 處理 |

**禁止**: utf8 (MySQL 的 utf8 = utf8mb3, 不支援 emoji)

## 7. RFC 流程（Convention 變更）

`locked_at` 寫入後修改本檔案的流程：
1. 提案者開 issue / PR 描述變更原因 + 影響範圍
2. PM + 至少一個 SD 同意
3. 通過後更新 `change_history`，bump `version`
4. 通知所有 in_progress TASK 的 SD 重新檢視 db-schema.md

## 8. 禁止項彙整

- ❌ 表名 PascalCase / camelCase
- ❌ 欄位 PascalCase / camelCase
- ❌ 直接 DROP COLUMN（必須三段式）
- ❌ 不可逆 migration（無 down）
- ❌ 修改已 push 的 migration（必須新增 migration 修正）
- ❌ Migration 檔名缺少時間戳前綴
- ❌ MySQL utf8（必須 utf8mb4）

### 專案特定禁止項

- ❌ **應用程式碼內寫 `ALTER TABLE` / `CREATE TABLE`**（既有 `web/auth/database.py:44-52` 用 `try: ALTER TABLE ADD COLUMN; except: pass` 是 brownfield 技術債）— 新增 schema 變更必須走正式 migration 檔案
- ❌ **依賴 Railway SQLite 持久化**（ephemeral storage，重啟即失資料）— 所有持久化資料必須走 Postgres
- ❌ **直接 DELETE FROM** 用戶資料（如 `favorites` 表 — 既有 `auth_router.py:246` 採硬刪除）— 新增的用戶可逆操作必須軟刪（`deleted_at` 欄位 + 應用層 filter）
- ❌ **無 `created_at` / `updated_at` 的新表**（既有 3 張表都缺 `updated_at` — brownfield grandfather；新表必補）
