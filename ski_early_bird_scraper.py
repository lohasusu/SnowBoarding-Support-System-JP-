"""
ski_early_bird_scraper.py
爬取日本滑雪場官網的票種與票價，輸出至 Excel，並預留資料庫寫入介面。

目標網址來源（優先順序）：
  1. urls.json  — 與本腳本同目錄，格式見 DEFAULT_TARGETS
  2. 程式內建的 DEFAULT_TARGETS（fallback）
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import openpyxl
from deep_translator import GoogleTranslator
from openpyxl.styles import Font, PatternFill, Alignment
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# ── 設定區 ──────────────────────────────────────────────────────────────────

OUTPUT_DIR = Path(r"D:\SideProject\測試產出檔案")
URLS_FILE  = Path(__file__).parent / "urls.json"

DEFAULT_TARGETS = [
    {"name": "白馬五龍雪場", "url": "https://www.hakubagoryu.com/", "note": "長野 Nagano"},
    {"name": "二世谷 Niseko United", "url": "https://www.niseko.ne.jp/", "note": "北海道 Hokkaido"},
]

# 票種相關關鍵字（日英）
TICKET_KEYWORDS = [
    "券", "パス", "チケット", "リフト", "大人", "子供", "こども", "シニア",
    "1日", "半日", "通し", "シーズン", "早割", "前売", "当日", "ナイター",
    "pass", "ticket", "adult", "child", "senior", "day", "half", "season",
    "lift", "early bird", "discount",
]

# 票價頁面常見子路徑（依可能性排序）
CANDIDATE_PATHS = [
    "/ticket", "/tickets", "/lift-ticket", "/price", "/prices",
    "/pass", "/lift", "/season", "/info", "/news",
]

# 日圓價格正則
PRICE_PATTERN = re.compile(
    r"[¥￥][\d,]+|[\d,]+\s*円|JPY\s*[\d,]+|[\d,]+\s*JPY",
    re.IGNORECASE,
)


# ── 資料結構 ─────────────────────────────────────────────────────────────────

@dataclass
class TicketItem:
    resort: str
    region: str
    source_url: str
    ticket_type: str
    ticket_type_zh: str      # 票種中文翻譯
    price: str
    scraped_at: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


# ── 翻譯工具 ─────────────────────────────────────────────────────────────────

_translate_cache: dict[str, str] = {}  # 避免重複翻譯同一票種
_translator = GoogleTranslator(source="ja", target="zh-TW")


def translate_ja_to_zh(text: str) -> str:
    """日文 → 繁體中文，失敗時回傳原文。結果快取避免重複呼叫。"""
    if text in _translate_cache:
        return _translate_cache[text]
    try:
        result = _translator.translate(text) or text
    except Exception:
        result = text
    _translate_cache[text] = result
    return result


# ── 工具函式 ─────────────────────────────────────────────────────────────────

def extract_prices(text: str) -> list[str]:
    return [m.group().strip() for m in PRICE_PATTERN.finditer(text)]


def is_ticket_related(text: str) -> bool:
    t = text.lower()
    return any(kw.lower() in t for kw in TICKET_KEYWORDS)


def load_targets() -> list[dict]:
    """urls.json があれば読む、なければ内蔵デフォルトを使う。"""
    if URLS_FILE.exists():
        try:
            data = json.loads(URLS_FILE.read_text(encoding="utf-8"))
            targets = [t for t in data if isinstance(t, dict) and "name" in t and "url" in t]
            if targets:
                print(f"[設定] 從 {URLS_FILE.name} 載入 {len(targets)} 個目標網址")
                return targets
            print(f"[警告] {URLS_FILE.name} 格式不符，改用內建預設。")
        except (json.JSONDecodeError, OSError) as e:
            print(f"[警告] 讀取 {URLS_FILE.name} 失敗（{e}），改用內建預設。")
    else:
        print(f"[設定] 找不到 {URLS_FILE.name}，使用內建預設。")
    return DEFAULT_TARGETS


# ── 票價擷取策略 ──────────────────────────────────────────────────────────────

async def _try_table_rows(page, resort, region, url, seen) -> list[TicketItem]:
    """策略 1：掃描 <table> 的每一行，找票種＋價格配對。"""
    items = []
    rows = await page.query_selector_all("table tr")
    for row in rows:
        cells = await row.query_selector_all("td, th")
        cell_texts = []
        for c in cells:
            try:
                cell_texts.append((await c.inner_text()).strip())
            except Exception:
                cell_texts.append("")

        row_text = " ".join(cell_texts)
        prices = extract_prices(row_text)
        if not prices:
            continue

        # 取第一個非價格的儲存格當票種名稱
        ticket_type = next(
            (t for t in cell_texts if t and not extract_prices(t)), ""
        )
        if not ticket_type or not is_ticket_related(ticket_type):
            continue

        for price in prices:
            key = f"{resort}||{ticket_type}||{price}"
            if key not in seen:
                seen.add(key)
                items.append(TicketItem(resort, region, url, ticket_type, translate_ja_to_zh(ticket_type), price))
    return items


async def _try_dt_dd(page, resort, region, url, seen) -> list[TicketItem]:
    """策略 2：掃描 <dt>/<dd> 配對（定義列表）。"""
    items = []
    dts = await page.query_selector_all("dt")
    for dt in dts:
        try:
            dt_text = (await dt.inner_text()).strip()
            dd_el   = await dt.evaluate_handle("el => el.nextElementSibling")
            dd_text = (await dd_el.inner_text()).strip() if dd_el else ""
        except Exception:
            continue

        prices = extract_prices(dd_text) or extract_prices(dt_text)
        if prices and is_ticket_related(dt_text):
            for price in prices:
                key = f"{resort}||{dt_text}||{price}"
                if key not in seen:
                    seen.add(key)
                    items.append(TicketItem(resort, region, url, dt_text, translate_ja_to_zh(dt_text), price))
    return items


async def _try_inline_elements(page, resort, region, url, seen) -> list[TicketItem]:
    """策略 3：掃描 p / li / span，找同時含票種關鍵字與價格的短文字塊。"""
    items = []
    elements = await page.query_selector_all("p, li, span, div")
    for el in elements:
        try:
            text = (await el.inner_text()).strip()
        except Exception:
            continue
        if not text or len(text) > 200:
            continue
        prices = extract_prices(text)
        if prices and is_ticket_related(text):
            for price in prices:
                key = f"{resort}||{text[:80]}||{price}"
                if key not in seen:
                    seen.add(key)
                    items.append(TicketItem(resort, region, url, text[:120], translate_ja_to_zh(text[:120]), price))
    return items


async def extract_tickets(page, url: str, resort: str, region: str, seen: set) -> list[TicketItem]:
    """三種策略依序嘗試，取最先有結果的。"""
    for strategy in (_try_table_rows, _try_dt_dd, _try_inline_elements):
        items = await strategy(page, resort, region, url, seen)
        if items:
            return items
    return []


# ── 爬蟲核心 ─────────────────────────────────────────────────────────────────

async def scrape_resort(browser, target: dict) -> list[TicketItem]:
    resort = target["name"]
    region = target.get("note", "")
    base_url = target["url"]
    seen: set[str] = set()
    results: list[TicketItem] = []
    page = await browser.new_page()

    try:
        print(f"[{resort}] 開啟: {base_url}")
        await page.goto(base_url, timeout=45_000, wait_until="networkidle")
        await page.wait_for_selector("body", timeout=10_000)

        results = await extract_tickets(page, base_url, resort, region, seen)

        # 首頁找不到時逐一嘗試候補子路徑
        if not results:
            for path in CANDIDATE_PATHS:
                sub_url = base_url.rstrip("/") + path
                try:
                    print(f"  嘗試: {sub_url}")
                    await page.goto(sub_url, timeout=30_000, wait_until="networkidle")
                    results = await extract_tickets(page, sub_url, resort, region, seen)
                    if results:
                        break
                except PlaywrightTimeoutError:
                    print(f"  逾時略過: {sub_url}")
                except Exception as e:
                    print(f"  錯誤 {sub_url}: {e}")

    except PlaywrightTimeoutError:
        print(f"[{resort}] 頁面載入逾時。")
    except Exception as e:
        print(f"[{resort}] 發生錯誤: {e}")
    finally:
        await page.close()

    return results


# ── Excel 輸出 ────────────────────────────────────────────────────────────────

HEADER = ["地區", "雪場名稱", "票種（日文）", "票種（中文）", "票價", "來源網址", "抓取時間"]
HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(bold=True, color="FFFFFF")


def save_to_excel(items: list[TicketItem], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    # 同一天有多個檔案時自動遞增序號
    seq = 1
    while True:
        filepath = output_dir / f"SNOWBOARD_TICKETS_{today}_{seq:03d}.xlsx"
        if not filepath.exists():
            break
        seq += 1

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "票種票價"

    # 標題列
    for col, header in enumerate(HEADER, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")

    # 資料列
    for row_idx, item in enumerate(items, 2):
        ws.cell(row=row_idx, column=1, value=item.region)
        ws.cell(row=row_idx, column=2, value=item.resort)
        ws.cell(row=row_idx, column=3, value=item.ticket_type)
        ws.cell(row=row_idx, column=4, value=item.ticket_type_zh)
        ws.cell(row=row_idx, column=5, value=item.price)
        ws.cell(row=row_idx, column=6, value=item.source_url)
        ws.cell(row=row_idx, column=7, value=item.scraped_at)

    # 自動欄寬
    for col in ws.columns:
        max_len = max((len(str(c.value)) for c in col if c.value), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 80)

    wb.save(filepath)
    return filepath


# ── 資料庫預留介面 ────────────────────────────────────────────────────────────
# 未來接 DB 時，於此實作 INSERT 邏輯。
# 建議資料表欄位：resort, region, source_url, ticket_type, price, scraped_at
#
# 範例（SQLAlchemy）：
#   with engine.begin() as conn:
#       conn.execute(text("""
#           INSERT INTO ski_tickets (resort, region, source_url, ticket_type, price, scraped_at)
#           VALUES (:resort, :region, :source_url, :ticket_type, :price, :scraped_at)
#       """), [asdict(item) for item in items])

def save_to_database(items: list[TicketItem]) -> None:
    """預留的資料庫寫入函式，補上連線邏輯即可啟用。"""
    if not items:
        return
    # TODO: 建立 DB 連線
    # TODO: 執行 parameterized INSERT
    # TODO: 關閉連線
    print(f"[DB] 預留介面：共 {len(items)} 筆待寫入資料庫（尚未實作）。")


# ── 主流程 ────────────────────────────────────────────────────────────────────

async def main() -> None:
    all_items: list[TicketItem] = []
    targets = load_targets()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            tasks = [scrape_resort(browser, t) for t in targets]
            for result in await asyncio.gather(*tasks):
                all_items.extend(result)
        finally:
            await browser.close()

    if all_items:
        excel_path = save_to_excel(all_items, OUTPUT_DIR)
        print(f"\n✓ Excel 已輸出：{excel_path}")
        print(f"  共 {len(all_items)} 筆票價資料。")
    else:
        print("\n未擷取到任何票價資料（網站可能為淡季、需登入或為 JS 動態載入）。")

    save_to_database(all_items)


if __name__ == "__main__":
    asyncio.run(main())
