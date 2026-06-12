---
document_id: "DBCON-CONVENTIONS-v1.0"
title: "資料庫慣例規範"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "PM"
status: "Living Document (Layer 2 conventions/)"
phase: "conventions"
locked_at: "{ISO time set by /sdlc:init Step 4.15 — empty / placeholder = unlocked}"
change_history:
  - version: "1.0"
    date: "{YYYY-MM-DD}"
    changes: "init"
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
| TASK 範圍前綴 | `[CUSTOMIZE: 是否需要 module 前綴 e.g. `auth_users` `billing_invoices`]` | 視專案規模 |

## 2. 欄位命名規範

| 類型 | 命名 | 範例 |
|------|------|------|
| 主鍵 | `id` | `BIGINT UNSIGNED AUTO_INCREMENT` 或 `UUID` — `[CUSTOMIZE]` |
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
    ON DELETE [CUSTOMIZE: RESTRICT|SET NULL|CASCADE]
    ON UPDATE CASCADE;
```

- 外鍵命名: `fk_{table}_{column}_{ref_table}`
- ON DELETE 預設 RESTRICT（保護資料），明確需要 cascade 才設定
- ON UPDATE 通常 CASCADE

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
| Charset | `utf8mb4` (MySQL) / `UTF8` (Postgres) | `[CUSTOMIZE]` |
| Collation | `utf8mb4_unicode_ci` | `[CUSTOMIZE: case-insensitive search 需求]` |

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

[CUSTOMIZE: 加入專案特定禁止項]
