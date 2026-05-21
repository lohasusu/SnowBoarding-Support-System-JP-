"""
site_analyzer.py
對 urls.json 中每個雪場網站做一次性結構分析：
  1. 找出最可能含票價的子頁面連結
  2. 截圖並儲存 HTML，供人工確認選擇器
  3. 自動推測 CSS 選擇器（table / dl / div card）
  4. 輸出 urls_analyzed.json，人工確認後可直接覆蓋 urls.json

使用方式：
  python site_analyzer.py                     # 分析全部
  python site_analyzer.py --name "Furano"     # 只分析指定網站（部分比對）
  python site_analyzer.py --concurrency 3     # 同時開幾個 browser tab（預設 3）
"""

import argparse
import asyncio
import json
import re
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# ── 路徑設定 ──────────────────────────────────────────────────────────────────
SCRIPT_DIR    = Path(__file__).parent
URLS_FILE     = SCRIPT_DIR / "urls.json"
ANALYSIS_DIR  = SCRIPT_DIR / "analysis"
SCREENSHOT_DIR = ANALYSIS_DIR / "screenshots"
HTML_DIR       = ANALYSIS_DIR / "html"
REPORT_FILE    = ANALYSIS_DIR / "analysis_report.json"
ANALYZED_URLS  = ANALYSIS_DIR / "urls_analyzed.json"

# ── 關鍵字 ────────────────────────────────────────────────────────────────────
TICKET_LINK_KW = [
    "ticket", "tickets", "lift", "price", "prices", "pass", "passes",
    "料金", "チケット", "券", "パス", "リフト", "シーズン", "早割", "前売",
    "rate", "rates", "fee", "fees", "ski", "snow", "winter",
]

PRICE_RE = re.compile(
    r"[¥￥][\d,]+|[\d,]+\s*円|JPY\s*[\d,]+|[\d,]+\s*JPY",
    re.IGNORECASE,
)

TICKET_KW = [
    "券", "パス", "チケット", "リフト", "大人", "子供", "こども", "シニア",
    "1日", "半日", "通し", "シーズン", "早割", "前売", "当日", "ナイター",
    "pass", "ticket", "adult", "child", "senior", "day", "half", "season",
    "lift", "early bird", "discount",
]


# ── 票價頁面連結發現 ──────────────────────────────────────────────────────────

def _score_link(href: str, text: str) -> int:
    """對連結評分：含越多關鍵字分數越高。"""
    combined = (href + " " + text).lower()
    return sum(1 for kw in TICKET_LINK_KW if kw.lower() in combined)


async def find_ticket_links(page, base_url: str) -> list[str]:
    """從當前頁面收集可能含票價資訊的內部連結，依評分排序後回傳前 5 個。"""
    try:
        links = await page.evaluate("""
            (baseUrl) => {
                const origin = new URL(baseUrl).origin;
                return Array.from(document.querySelectorAll('a[href]'))
                    .map(a => ({href: a.href, text: a.textContent.trim()}))
                    .filter(l => {
                        try { return new URL(l.href).origin === origin; }
                        catch { return false; }
                    });
            }
        """, base_url)
    except Exception:
        return []

    scored = [(l["href"], l["text"], _score_link(l["href"], l["text"])) for l in links]
    scored = [(h, t, s) for h, t, s in scored if s > 0]
    scored.sort(key=lambda x: -x[2])

    seen: set[str] = set()
    result = []
    for href, _, _ in scored:
        if href not in seen:
            seen.add(href)
            result.append(href)
        if len(result) >= 5:
            break
    return result


# ── CSS 選擇器自動推測 ────────────────────────────────────────────────────────

_SUGGEST_JS = """
() => {
    const priceRe = /[¥￥][\\d,]+|[\\d,]+\\s*円|JPY\\s*[\\d,]+/;
    const ticketKw = ['券','パス','チケット','リフト','大人','子供','シニア',
                      '1日','半日','シーズン','早割','前売','当日','ナイター',
                      'pass','ticket','adult','child','senior','day','lift'];

    function hasPrice(el) { return priceRe.test(el.textContent); }
    function hasTicket(el) {
        const t = el.textContent.toLowerCase();
        return ticketKw.some(k => t.includes(k.toLowerCase()));
    }
    function bestSelector(el) {
        if (el.id) return '#' + CSS.escape(el.id);
        const cls = Array.from(el.classList).filter(c => c.length > 1 && !/^[0-9]/.test(c));
        if (cls.length) return el.tagName.toLowerCase() + '.' + cls.slice(0,2).map(c=>CSS.escape(c)).join('.');
        return null;
    }

    const suggestions = [];

    // 策略 A：含票價且含票種關鍵字的 <table>
    document.querySelectorAll('table').forEach(table => {
        if (!hasPrice(table) || !hasTicket(table)) return;
        const sel = bestSelector(table) || 'table';
        const rows = Array.from(table.querySelectorAll('tr'))
            .filter(r => hasPrice(r) && hasTicket(r))
            .slice(0, 3)
            .map(r => r.textContent.replace(/\\s+/g,' ').trim().substring(0,120));
        suggestions.push({type:'table', container:sel, row_selector:'tr', samples:rows});
    });

    // 策略 B：<dl> 定義列表
    document.querySelectorAll('dl').forEach(dl => {
        if (!hasPrice(dl) || !hasTicket(dl)) return;
        const sel = bestSelector(dl) || 'dl';
        const pairs = [];
        dl.querySelectorAll('dt').forEach(dt => {
            const dd = dt.nextElementSibling;
            if (dd && dd.tagName === 'DD' && hasPrice(dd) && hasTicket(dt)) {
                pairs.push(dt.textContent.trim().substring(0,60) + ' → ' + dd.textContent.trim().substring(0,40));
            }
        });
        if (pairs.length) suggestions.push({type:'dl', container:sel, row_selector:'dt', samples:pairs.slice(0,3)});
    });

    // 策略 C：div/section 裡的「票種 + 價格」卡片組合
    const priceEls = Array.from(document.querySelectorAll('*'))
        .filter(el => {
            if (!['SPAN','P','DIV','TD','LI','DD'].includes(el.tagName)) return false;
            return priceRe.test(el.textContent) && el.textContent.trim().length < 80;
        });

    priceEls.forEach(priceEl => {
        const parent = priceEl.parentElement;
        if (!parent) return;
        const siblings = Array.from(parent.children);
        const nameEl = siblings.find(s => s !== priceEl && hasTicket(s) && s.textContent.trim().length < 80);
        if (!nameEl) return;
        const containerSel = bestSelector(parent);
        if (!containerSel) return;
        const nameSel = nameEl.tagName.toLowerCase() + (nameEl.className ? '.' + nameEl.className.split(' ')[0] : '');
        const priceSel = priceEl.tagName.toLowerCase() + (priceEl.className ? '.' + priceEl.className.split(' ')[0] : '');
        suggestions.push({
            type:'card',
            container: containerSel,
            name_selector: nameSel,
            price_selector: priceSel,
            samples: [(nameEl.textContent.trim()||'').substring(0,60)
                       + ' → ' + (priceEl.textContent.trim()||'').substring(0,40)]
        });
    });

    return suggestions.slice(0, 8);
}
"""


async def suggest_selectors(page) -> list[dict]:
    try:
        return await page.evaluate(_SUGGEST_JS)
    except Exception as e:
        return [{"error": str(e)}]


# ── 單一網站分析 ──────────────────────────────────────────────────────────────

async def analyze_resort(semaphore, browser, target: dict) -> dict:
    name     = target["name"]
    base_url = target["url"]
    region   = target.get("note", "")

    result = {
        "name": name,
        "url": base_url,
        "note": region,
        "status": "pending",
        "ticket_url": None,
        "selectors": {},
        "candidate_pages": [],
        "selector_hints": [],
        "screenshot": None,
        "html_file": None,
        "error": None,
    }

    async with semaphore:
        page = await browser.new_page()
        try:
            print(f"[{name}] 載入首頁 ...")
            await page.goto(base_url, timeout=40_000, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)  # JS 動態載入緩衝

            # 從首頁尋找票價相關連結
            candidates = await find_ticket_links(page, base_url)
            result["candidate_pages"] = candidates
            print(f"[{name}] 找到 {len(candidates)} 個候補連結")

            # 依序嘗試候補頁面，取第一個有價格的
            best_page_url = None
            for url in [base_url] + candidates[:4]:
                if url != base_url:
                    try:
                        await page.goto(url, timeout=30_000, wait_until="domcontentloaded")
                        await page.wait_for_timeout(2500)  # 候補頁面同樣留時間給 JS
                    except PlaywrightTimeoutError:
                        continue
                    except Exception:
                        continue

                page_text = await page.inner_text("body")
                if PRICE_RE.search(page_text):
                    best_page_url = url
                    print(f"[{name}] 找到含票價頁面: {url}")
                    break

            if not best_page_url:
                result["status"] = "no_price_found"
                print(f"[{name}] 未找到含票價的頁面")
                return result

            # 截圖
            safe_name = re.sub(r'[^\w\-]', '_', name)[:40]
            ss_path = SCREENSHOT_DIR / f"{safe_name}.png"
            await page.screenshot(path=str(ss_path), full_page=True)
            result["screenshot"] = str(ss_path)

            # 儲存 HTML
            html_path = HTML_DIR / f"{safe_name}.html"
            html_content = await page.content()
            html_path.write_text(html_content, encoding="utf-8")
            result["html_file"] = str(html_path)

            # 自動推測選擇器
            hints = await suggest_selectors(page)
            result["selector_hints"] = hints

            # 如果有推測結果，設定第一個作為預設（人工確認後可修改）
            if hints and hints[0].get("type") in ("table", "dl", "card") and not hints[0].get("error"):
                h = hints[0]
                if h["type"] == "table":
                    result["selectors"] = {
                        "_note": "自動推測，請人工確認並補上 ticket_name / ticket_price 選擇器",
                        "container": h.get("container", ""),
                        "row": h.get("row_selector", "tr"),
                    }
                elif h["type"] == "dl":
                    result["selectors"] = {
                        "_note": "自動推測，請人工確認",
                        "type": "dl",
                        "container": h.get("container", "dl"),
                    }
                elif h["type"] == "card":
                    result["selectors"] = {
                        "_note": "自動推測，請人工確認",
                        "type": "card",
                        "container": h.get("container", ""),
                        "ticket_name": h.get("name_selector", ""),
                        "ticket_price": h.get("price_selector", ""),
                    }

            result["ticket_url"] = best_page_url if best_page_url != base_url else None
            result["status"] = "analyzed"

        except PlaywrightTimeoutError:
            result["status"] = "timeout"
            result["error"] = "頁面載入逾時"
            print(f"[{name}] 逾時")
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"[{name}] 錯誤: {e}")
        finally:
            await page.close()

    return result


# ── 輸出 ──────────────────────────────────────────────────────────────────────

def build_analyzed_urls(targets: list[dict], reports: list[dict]) -> list[dict]:
    """將分析結果合併回原始 targets 格式，輸出可直接編輯的 urls_analyzed.json。"""
    report_map = {r["name"]: r for r in reports}
    result = []
    for t in targets:
        entry = dict(t)
        r = report_map.get(t["name"])
        if r:
            if r.get("ticket_url"):
                entry["ticket_url"] = r["ticket_url"]
            if r.get("selectors"):
                entry["selectors"] = r["selectors"]
        result.append(entry)
    return result


# ── 主流程 ────────────────────────────────────────────────────────────────────

async def main(filter_name: str | None, concurrency: int) -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    HTML_DIR.mkdir(parents=True, exist_ok=True)

    if not URLS_FILE.exists():
        print(f"找不到 {URLS_FILE}，請先建立 urls.json。")
        return

    targets: list[dict] = json.loads(URLS_FILE.read_text(encoding="utf-8"))
    if filter_name:
        targets = [t for t in targets if filter_name.lower() in t["name"].lower()]
        if not targets:
            print(f"找不到名稱包含「{filter_name}」的網站。")
            return
        print(f"過濾後分析 {len(targets)} 個網站: {[t['name'] for t in targets]}")
    else:
        print(f"共 {len(targets)} 個網站待分析")

    semaphore = asyncio.Semaphore(concurrency)
    reports = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            tasks = [analyze_resort(semaphore, browser, t) for t in targets]
            reports = await asyncio.gather(*tasks)
        finally:
            await browser.close()

    reports = list(reports)

    # 儲存完整分析報告
    REPORT_FILE.write_text(
        json.dumps(reports, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n分析報告: {REPORT_FILE}")

    # 儲存可編輯的 urls_analyzed.json
    analyzed = build_analyzed_urls(targets, reports)
    ANALYZED_URLS.write_text(
        json.dumps(analyzed, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"可編輯 URLs: {ANALYZED_URLS}")

    # 摘要
    success  = sum(1 for r in reports if r["status"] == "analyzed")
    no_price = sum(1 for r in reports if r["status"] == "no_price_found")
    errors   = sum(1 for r in reports if r["status"] in ("timeout", "error"))
    print(f"\n結果: 成功={success}, 未找到票價={no_price}, 錯誤={errors}")
    print(f"截圖目錄: {SCREENSHOT_DIR}")
    print(f"HTML 目錄: {HTML_DIR}")
    print(f"\n下一步: 開啟 {ANALYZED_URLS}")
    print("  對每個網站：確認 ticket_url 及 selectors 欄位，")
    print("  確認無誤後可覆蓋 urls.json 供主爬蟲使用。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="雪場網站結構分析工具")
    parser.add_argument("--name", help="只分析名稱包含此字串的網站")
    parser.add_argument("--concurrency", type=int, default=3, help="並行分析數量（預設 3）")
    args = parser.parse_args()
    asyncio.run(main(args.name, args.concurrency))
