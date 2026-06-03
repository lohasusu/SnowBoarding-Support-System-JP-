---
document_id: "SD-STYLE-{TASK_ID}-v1.0"
title: "視覺風格方向"
version: "1.0"
date: "{YYYY-MM-DD}"
author: "UIUX"
status: "Draft"
task_id: "{TASK-ID}"
phase: "uiux"
source_documents:
  - "REQ-{TASK_ID}-v1.0"
  - "FUNC-{TASK_ID}-v1.0"
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

# 視覺風格方向（Style Direction）

> **用途**: 記錄產品的視覺風格決策與設計語言。此文件在 TASK-001 建立後放入 shared 層，TASK-002+ 唯讀引用。
> **位置**: `.sdlc/shared/apps/{app}/style-direction.md`

## 1. 產品類型分析

| 項目 | 內容 |
|------|------|
| 產品類型 | {Admin Panel / Dashboard / SaaS Tool / E-Commerce / Fintech / CMS / DevTool / 其他} |
| 判斷依據 | {從 BA 需求中推導的理由，引用 FR-ID} |
| 目標使用者 | {描述目標使用者角色與使用情境} |
| 使用頻率 | {每日高頻 / 偶爾使用 / 一次性操作} |
| 資訊密度 | {高密度（數據儀表板）/ 中密度（管理後台）/ 低密度（簡單表單）} |

## 2. Pencil Style 選擇

| 項目 | 選擇 | 理由 |
|------|------|------|
| Style 原型 | {Soft Bento / Aerial Gravitas / Artisan Editorial / Cinematic Alternating / Editorial Scientific / Illustrated Warm / Inline Friendly / Monumental Editorial / Product Demo / Spatial Plus} | {為什麼選這個 style} |
| Color Palette | {Carbon Frost / Deep Space Neon / Fern Journal / Forest Sage / Heritage Warmth / Parchment Gold / Tangerine Orbit / Terminal Green / Warm Concrete / Warm Linen} | {為什麼選這個配色} |
| Elevation | {Gentle Lift / Sharp Depth / Soft Cloud / Soft Lift} | {為什麼選這個陰影策略} |
| Roundness | {Basic Roundness} | — |
| Headings 字體 | {Anton / Funnel Sans / Geist / Geist Mono / IBM Plex Mono / Inter / Newsreader / Playfair Display} | {為什麼選這個字體} |
| Body 字體 | {同上選項} | {理由} |
| Captions 字體 | {同上選項} | {理由} |
| Data 字體 | {同上選項，建議等寬字體} | {理由} |

## 3. 設計語言摘要

> 以下內容來自 Pencil `get_guidelines("style", "{選中Style}", {params})` 的回傳結果。

### Identity（設計識別）
{從 Pencil Style 規範複製的 Identity 描述}

### Composition（構圖規則）
{從 Pencil Style 規範複製的 Composition 規則}

### Spatial Density（空間密度）
{從 Pencil Style 規範複製的 Spatial Density 指南}

### Scale Contrast（尺度對比）
{從 Pencil Style 規範複製的 Scale Contrast 規則}

### Typography（字體使用規則）
{從 Pencil Style 規範複製的 Typography 規則}

### Shape（形狀規則）
{從 Pencil Style 規範複製的 Shape 規則}

### Color Rules（色彩規則）
{從 Pencil Style 規範複製的 Color Rules}

### Separation（分隔規則）
{從 Pencil Style 規範複製的 Separation 規則}

## 4. 色彩系統（從 Pencil Style 取得）

| Pencil Token | 色碼 | 用途 |
|-------------|------|------|
| surface.primary | {#hex} | 頁面背景 |
| surface.secondary | {#hex} | 卡片/區塊背景 |
| surface.inverse | {#hex} | 反轉背景（深色區塊） |
| foreground.primary | {#hex} | 主要文字 |
| foreground.secondary | {#hex} | 次要文字 |
| foreground.muted | {#hex} | 最淡文字 |
| foreground.inverse | {#hex} | 反轉文字（深色背景上） |
| accent.primary | {#hex} | 強調色（主要操作） |

## 5. 陰影系統（從 Pencil Elevation 取得）

| Token | 定義 | 用途 |
|-------|------|------|
| shadow.sm | {Pencil elevation 定義} | {用途描述} |
| shadow.md | {若有} | {用途描述} |
| shadow.lg | {若有} | {用途描述} |

## 6. 圓角系統（從 Pencil Roundness 取得）

| Token | 值 | 用途 |
|-------|-----|------|
| rounded.sm | {值}px | {用途} |
| rounded.md | {值}px | {用途} |
| rounded.lg | {值}px | {用途} |
| rounded.xl | {值}px | {用途} |
| rounded.full | 9999px | 全圓（pill 按鈕、tag） |

## 7. 設計反模式（MUST AVOID）

| 反模式 | 正確做法 |
|--------|---------|
| 所有頁面使用同一個預設藍色 | 使用 Pencil Style 的完整 Palette |
| 所有陰影用同一個 `0 1px 2px rgba(0,0,0,0.05)` | 使用 Pencil Elevation 定義的陰影層級 |
| 所有字體使用 Inter 14px | 使用 4-slot 字體系統（Headings/Body/Captions/Data） |
| 元件間距隨機 | 遵循 Design System Guide 的 spacing 參考表 |
| 每個區域相同視覺權重 | 遵循 Dominant Region Rule |
| 所有功能塞進一頁 | 遵循 Progressive Disclosure |
| 裝飾性元素過多 | 遵循 Constraint Over Decoration |

## 8. 追溯

| 項目 | 來源 |
|------|------|
| 產品類型判斷 | {FR-ID / 使用者原文} |
| Style 選擇 | Pencil MCP `get_guidelines("style", ...)` |
| 設計原則 | Pencil MCP `get_guidelines("guide", "Web App")` |
