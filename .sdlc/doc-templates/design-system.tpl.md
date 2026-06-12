---
document_id: "DS-{TASK_ID}-v1.0"
title: "設計系統規範"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "UIUX"
status: "Draft"
task_id: "{TASK-ID}"
phase: "uiux"
source_documents:
  - "ARCH-{TASK_ID}-v1.0"
  - "FUNC-{TASK_ID}-v1.0"
  - "FIELD-{TASK_ID}-v1.0"
change_history:
  - version: "1.0"
    date: "{YYYY-MM-DD}"
    changes: "初始版本"
    author: "UIUX"
approval:
  reviewer: "PM"
  date: ""
  result: "Pending"
  notes: ""
---

# 設計系統規範（Design System）

## 0. 設計參考來源

| 項目 | 值 |
|------|-----|
| Pencil Style | {選用的 Style 原型名稱} |
| Color Palette | {選用的 Palette 名稱} |
| Elevation | {選用的 Elevation 名稱} |
| 字體配置 | Headings: {字體} / Body: {字體} / Captions: {字體} / Data: {字體} |
| 來源文件 | style-direction.md |

> **規則**: 以下所有 Token 值必須從 style-direction.md 記錄的 Pencil Style 規範轉換而來，
> 不可自行硬編碼預設值（如 #3B82F6）。

## 1. 色彩系統

### 主色（Primary）
| Token | 色碼 | 用途 |
|-------|------|------|
| color.primary.50 | {#hex} | 最淺背景 |
| color.primary.100 | {#hex} | 淺背景 |
| color.primary.200 | {#hex} | 邊框 |
| color.primary.300 | {#hex} | 禁用 |
| color.primary.400 | {#hex} | Hover |
| color.primary.500 | {#hex} | 主色（預設） |
| color.primary.600 | {#hex} | Active |
| color.primary.700 | {#hex} | 深色 |
| color.primary.800 | {#hex} | 更深 |
| color.primary.900 | {#hex} | 最深 |

### 輔色（Secondary）
| Token | 色碼 | 用途 |
|-------|------|------|
| color.secondary.500 | {#hex} | 輔色預設 |

### 功能色
| Token | 色碼 | 用途 |
|-------|------|------|
| color.success.500 | {#hex} | 成功 |
| color.warning.500 | {#hex} | 警告 |
| color.error.500 | {#hex} | 錯誤 |
| color.info.500 | {#hex} | 資訊 |

### 中性色（Neutral）
| Token | 色碼 | 用途 |
|-------|------|------|
| color.neutral.0 | #FFFFFF | 白色背景 |
| color.neutral.50 | {#hex} | 灰色背景 |
| color.neutral.100 | {#hex} | 邊框 |
| color.neutral.500 | {#hex} | 次要文字 |
| color.neutral.800 | {#hex} | 主要文字 |
| color.neutral.900 | {#hex} | 標題文字 |

## 2. 字體系統

### 字型
| Token | 值 | 用途 |
|-------|-----|------|
| font.family.primary | {字型名} | 主要字型 |
| font.family.mono | {字型名} | 等寬字型 |

### 字體大小
| Token | 大小 | 行高 | 粗細 | 用途 |
|-------|------|------|------|------|
| font.display.lg | 36px | 1.2 | 700 | 大標題 |
| font.display.md | 30px | 1.2 | 700 | 中標題 |
| font.heading.lg | 24px | 1.3 | 600 | H1 |
| font.heading.md | 20px | 1.3 | 600 | H2 |
| font.heading.sm | 16px | 1.4 | 600 | H3 |
| font.body.lg | 18px | 1.5 | 400 | 大段文字 |
| font.body.md | 16px | 1.5 | 400 | 預設文字 |
| font.body.sm | 14px | 1.5 | 400 | 小文字 |
| font.caption | 12px | 1.4 | 400 | 說明文字 |

## 3. 間距系統（8px Grid）

| Token | 值 | 用途 |
|-------|-----|------|
| spacing.xs | 4px | 最小間距 |
| spacing.sm | 8px | 小間距 |
| spacing.md | 16px | 中間距（預設） |
| spacing.lg | 24px | 大間距 |
| spacing.xl | 32px | 特大間距 |
| spacing.2xl | 48px | 區塊間距 |
| spacing.3xl | 64px | 頁面間距 |

## 4. 陰影系統

> **來源**: 從 style-direction.md 的 Pencil Elevation 定義轉換。
> 可使用多層陰影組合營造更自然的深度效果。

| Token | 值 | 用途 |
|-------|-----|------|
| shadow.sm | {從 Pencil Elevation 取得} | 輕微陰影（卡片、輸入框） |
| shadow.md | {從 Pencil Elevation 取得} | 中等陰影（下拉選單、Tooltip） |
| shadow.lg | {從 Pencil Elevation 取得} | 大陰影（Modal、Drawer） |
| shadow.xl | {從 Pencil Elevation 取得} | 特大陰影（全螢幕 overlay） |

### 多層陰影範例（若 Style 需要）
```css
/* 例: Soft Lift — 單層輕柔 */
shadow.sm: 0 1px 2px rgba(0,0,0,0.04);

/* 例: Sharp Depth — 雙層銳利 */
shadow.lg: 0 12px 24px rgba(0,0,0,0.7);

/* 例: Notion-style — 三層複合 */
shadow.card: 
  0 0 0 1px rgba(0,0,0,0.08),
  0 4px 18px rgba(0,0,0,0.04),
  0 1px 2px rgba(0,0,0,0.02);
```

## 5. 動畫系統

| Token | 值 | 用途 |
|-------|-----|------|
| transition.fast | 100ms ease-in-out | 快速過渡 |
| transition.default | 150ms ease-in-out | 預設過渡 |
| transition.slow | 300ms ease-in-out | 慢速過渡 |
| transition.enter | 200ms ease-out | 進入動畫 |
| transition.exit | 150ms ease-in | 離開動畫 |

## 6. 響應式斷點

| Token | 值 | 說明 |
|-------|-----|------|
| breakpoint.mobile | 375px | 手機 |
| breakpoint.tablet | 768px | 平板 |
| breakpoint.desktop | 1024px | 桌面 |
| breakpoint.wide | 1440px | 寬螢幕 |

## 7. 圓角系統

| Token | 值 | 用途 |
|-------|-----|------|
| radius.sm | 4px | 小圓角 |
| radius.md | 8px | 中圓角 |
| radius.lg | 12px | 大圓角 |
| radius.xl | 16px | 特大圓角 |
| radius.full | 9999px | 全圓 |

> **注意**: 共用元件庫和 UI 模式（Modal/Dialog/Toast/Drawer）定義已移至 `component-spec.md`。
> 本文件僅定義 Design Token 值。
