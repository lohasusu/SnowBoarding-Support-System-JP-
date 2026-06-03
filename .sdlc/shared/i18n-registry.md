---
document_id: "I18N-SHARED-v1.0"
title: "i18n Key 登記簿"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "UIUX"
status: "Living Document"
phase: "shared"
change_history:
  - version: "1.0"
    date: "{YYYY-MM-DD}"
    changes: "初始建立"
    author: "UIUX"
---

# i18n Key 登記簿

> **用途**: 建立 i18n Key 與 COMP 文字屬性的一對一綁定，確保 UIUX wireframes / SD fe-api-mapping / FE 原始碼三方 UI Copy 一致。
> **規範依據**: `rules/sdlc-external-id-binding.md` 規則 2、`MASTER-INDEX.md` §6、`rules/sdlc-fe.md` 規則 5。
> **維護者**: UIUX（新增）、SD（對齊 API 錯誤訊息）、FE（實作後登記 source path）。
> **啟用條件**: 專案為多語言或 UIUX 繪製時有可翻譯文字時 MANDATORY。

## 1. Key 命名規範

**格式**: `{ns}.{domain}.{name}`

| 層級 | 名稱 | 說明 | 範例 |
|------|------|------|------|
| ns | 命名空間 | 跨模組共用或模組專屬 | `common` / `user` / `order` |
| domain | 類別 | 文字屬性類型 | `button` / `label` / `placeholder` / `tooltip` / `error` / `toast` / `dialog` / `empty` |
| name | 具體鍵 | 描述性名稱（kebab-case） | `submit` / `email-required` / `user-not-found` |

**範例**:
- `common.button.submit` — 共用提交按鈕
- `user.label.email` — 使用者模組 Email 欄位標籤
- `order.error.amount-invalid` — 訂單模組金額驗證錯誤

**禁止**:
- 全大寫或 snake_case（保留給 ERR-alias）
- 中文或非 ASCII（Key 只能用英文）
- 超過 4 層（`common.button.primary.hover.disabled` → 改用狀態屬性而非 Key）

## 2. i18n Key 清單（主表）

| i18n Key | 預設文字（{預設語系}）| 其他語系 | 綁定 COMP | 文字屬性 | 來源 | 登記於 TASK |
|----------|---------------------|----------|----------|---------|------|-----------|
| common.button.submit | 提交 | {en: Submit} | COMP-001 | label | FR-001 | TASK-001 |
| user.label.email | 電子信箱 | {en: Email} | COMP-012 | label | FR-002 | TASK-001 |
| user.error.email-required | 請輸入電子信箱 | {en: Email is required} | COMP-012 | error | FR-002/AC-003 | TASK-001 |

**欄位說明**:
- **綁定 COMP**: 單一 Key 可綁定多個 COMP（`COMP-001, COMP-042`），表示跨元件共用
- **文字屬性**: `label` / `placeholder` / `tooltip` / `error` / `toast` / `dialog-title` / `dialog-body` / `empty-state` / `aria-label`
- **來源**: 追溯到 FR-NNN / AC-NNN / BR-NNN / ERR-{DOMAIN}-NNN

## 3. ERR 錯誤訊息綁定

所有 `ERR-{DOMAIN}-NNN` 在 `error-codes.md` 定義的 `user_message` 必須對應一個 i18n Key：

| ERR-ID | i18n Key | 預設文字 |
|--------|----------|---------|
| ERR-AUTH-001 | auth.error.invalid-credentials | 帳號或密碼錯誤 |
| ERR-VAL-002 | common.error.required-field | 此欄位為必填 |

> 由 SD 在 `error-codes.md` 完成後同步建立，FE 實作時從此表讀取。

## 4. FE 原始碼綁定

FE 實作後必須在此表登記每個 Key 在原始碼中的路徑：

| i18n Key | 檔案路徑 | 登記於 TASK |
|----------|---------|-----------|
| common.button.submit | src/locales/zh-TW/common.json | TASK-001 |

## 5. 完整性驗證（執行式 Bash）

### 5.1 Key 唯一性（禁止重複 Key — 僅檢查第 2 節主表）

```bash
awk '/^## 2\./,/^## 3\./' .sdlc/shared/i18n-registry.md \
  | grep -oE '^\| [a-z]+\.[a-z-]+\.[a-z-]+ ' \
  | sort | uniq -d | grep -q . && echo "FAIL: 發現重複 Key" || echo "PASS: Key 唯一"
```

### 5.2 Key 格式正確性（必須符合 {ns}.{domain}.{name}）

```bash
grep -oE '^\| [^ ]+' .sdlc/shared/i18n-registry.md \
  | grep -v '^| i18n Key' \
  | grep -v '^| ---' \
  | awk -F'|' '{print $2}' \
  | tr -d ' ' \
  | grep -vE '^[a-z]+\.[a-z-]+\.[a-z-]+$' \
  | grep -q . && echo "FAIL: 有 Key 不符合格式" || echo "PASS: Key 格式全部正確"
```

### 5.3 綁定 COMP 存在性（所有 Key 綁定的 COMP 必須存在於 component-index.md）

```bash
# 取出所有 i18n-registry.md 第 2 節的 COMP-NNN
grep -oE 'COMP-[0-9]{3}' .sdlc/shared/i18n-registry.md | sort -u > /tmp/i18n_comps.txt
# 取出 component-index.md 的 COMP-NNN
grep -oE 'COMP-[0-9]{3}' .sdlc/shared/component-index-*.md | grep -oE 'COMP-[0-9]{3}' | sort -u > /tmp/actual_comps.txt
# 差集應為空
comm -23 /tmp/i18n_comps.txt /tmp/actual_comps.txt | grep -q . \
  && echo "FAIL: i18n 綁定不存在的 COMP" || echo "PASS: 所有綁定 COMP 存在"
```

### 5.4 ERR 訊息全綁定（所有 ERR-{DOMAIN}-NNN 的 user_message 必須在第 3 節）

```bash
# 取出 error-codes.md 的所有 ERR-ID
grep -oE 'ERR-[A-Z]+-[0-9]{3}' .sdlc/shared/error-codes.md | sort -u > /tmp/err_ids.txt
# 取出 i18n-registry.md 第 3 節的 ERR-ID
awk '/^## 3\./,/^## 4\./' .sdlc/shared/i18n-registry.md | grep -oE 'ERR-[A-Z]+-[0-9]{3}' | sort -u > /tmp/err_bound.txt
# 差集應為空
comm -23 /tmp/err_ids.txt /tmp/err_bound.txt | grep -q . \
  && echo "FAIL: 有 ERR 未綁定 i18n Key" || echo "PASS: 所有 ERR 已綁定"
```

### 5.5 FE 原始碼孤兒檢查（已宣告的 Key 必須在 FE 檔案中使用）

> FE 實作後執行：

```bash
# 所有登記的 Key
grep -oE '^\| [a-z]+\.[a-z-]+\.[a-z-]+' .sdlc/shared/i18n-registry.md \
  | awk -F'| ' '{print $2}' | sort -u > /tmp/declared.txt
# 原始碼中實際使用的 Key（假設用 t('key') 或 i18n.t("key")）
grep -rhoE "t\(['\"][a-z]+\.[a-z-]+\.[a-z-]+['\"]" src/ 2>/dev/null \
  | grep -oE "[a-z]+\.[a-z-]+\.[a-z-]+" | sort -u > /tmp/used.txt
# 已宣告但未使用
comm -23 /tmp/declared.txt /tmp/used.txt > /tmp/orphan.txt
[ -s /tmp/orphan.txt ] && echo "WARN: 有孤兒 Key（宣告但未使用）" || echo "PASS: 無孤兒 Key"
# 已使用但未宣告
comm -13 /tmp/declared.txt /tmp/used.txt > /tmp/undeclared.txt
[ -s /tmp/undeclared.txt ] && echo "FAIL: 有未宣告 Key（程式碼硬編碼）" || echo "PASS: 所有 Key 已宣告"
```

### 5.6 自我驗證檢查清單

- [ ] 第 1 節格式規範無誤
- [ ] 第 2 節所有 Key 通過 5.1 唯一性、5.2 格式正確性
- [ ] 第 2 節所有綁定 COMP 通過 5.3 存在性
- [ ] 第 3 節所有 ERR 通過 5.4 全綁定
- [ ] FE 實作後通過 5.5 孤兒/未宣告檢查

> 任一驗證失敗 → 扣 10 分 / 項，分數 < 90 不得交付。

## 6. 變更追蹤

| 日期 | 舊 Key | 新 Key | 原因 | 操作者 | 關聯 TASK |
|------|--------|--------|------|-------|----------|

> **禁止**: 直接修改或刪除已使用的 Key。必須先標記 `[DEPRECATED]`，移除 FE 引用後再刪除。
