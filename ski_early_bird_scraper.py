"""
ski_early_bird_scraper.py
爬取日本滑雪場（白馬五龍、二世谷）官網的 Early Bird / 早鳥 優惠公告，
輸出至 Excel，並預留資料庫寫入介面。
"""

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# ── 設定區 ──────────────────────────────────────────────────────────────────

OUTPUT_DIR = Path(r"D:\SideProject\測試產出檔案")

TARGETS = [
    {"name": "白馬五龍雪場", "url": "https://www.hakubagoryu.com/"},
    {"name": "二世谷 (Niseko United)", "url": "https://www.niseko.ne.jp/"},
]

KEYWORDS = ["Early Bird", "early bird", "早鳥", "アーリーバード"]

# 偵測日圓價格的正則
PRICE_PATTERN = re.compile(
    r"(¥|￥|JPY|円)[\s,\d]+|[\d,]+\s*(円|¥|￥|JPY)|[\d,]+\s*yen",
    re.IGNORECASE,
)

# 首頁找不到時，額外嘗試的子路徑
CANDIDATE_PATHS = ["/news", "/info", "/season", "/tickets", "/lift"]


# ── 資料結構 ─────────────────────────────────────────────────────────────────

@dataclass
class FoundItem:
    resort: str
    source_url: str
    keyword: str
    text: str
    prices: list[str] = field(default_factory=list)
    scraped_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


# ── 工具函式 ─────────────────────────────────────────────────────────────────

def extract_prices(text: str) -> list[str]:
    """從文字中提取所有價格字串。"""
    return [m.group().strip() for m in PRICE_PATTERN.finditer(text)]


def contains_keyword(text: str) -> str | None:
    """若文字含有任一關鍵字，回傳該關鍵字；否則回傳 None。"""
    for kw in KEYWORDS:
        if kw in text:
            return kw
    return None


# ── 爬蟲核心 ─────────────────────────────────────────────────────────────────

async def scrape_page(page, url: str, resort_name: str, seen: set) -> list[FoundItem]:
    """爬取單一頁面，回傳找到的 FoundItem 清單。"""
    results = []
    elements = await page.query_selector_all(
        "p, h1, h2, h3, h4, h5, li, a, span, div.news, div.info, article, section"
    )
    for el in elements:
        try:
            text = (await el.inner_text()).strip()
        except Exception:
            continue

        if not text or text in seen:
            continue

        kw = contains_keyword(text)
        if kw:
            seen.add(text)
            results.append(FoundItem(
                resort=resort_name,
                source_url=url,
                keyword=kw,
                text=text[:500],  # 避免單筆文字過長
                prices=extract_prices(text),
            ))
    return results


async def scrape_resort(browser, target: dict) -> list[FoundItem]:
    """開啟瀏覽器分頁，爬取指定雪場的首頁與備用子頁面。"""
    results: list[FoundItem] = []
    seen: set[str] = set()
    page = await browser.new_page()

    try:
        print(f"[{target['name']}] 開啟: {target['url']}")
        await page.goto(target["url"], timeout=30_000, wait_until="domcontentloaded")
        await page.wait_for_selector("body", timeout=10_000)

        results = await scrape_page(page, target["url"], target["name"], seen)

        # 首頁無結果時逐一嘗試子頁面
        if not results:
            for path in CANDIDATE_PATHS:
                sub_url = target["url"].rstrip("/") + path
                try:
                    print(f"  嘗試子頁面: {sub_url}")
                    await page.goto(sub_url, timeout=20_000, wait_until="domcontentloaded")
                    results = await scrape_page(page, sub_url, target["name"], seen)
                    if results:
                        break
                except PlaywrightTimeoutError:
                    print(f"  逾時略過: {sub_url}")
                except Exception as e:
                    print(f"  錯誤 {sub_url}: {e}")

    except PlaywrightTimeoutError:
        print(f"[{target['name']}] 頁面載入逾時。")
    except Exception as e:
        print(f"[{target['name']}] 發生錯誤: {e}")
    finally:
        await page.close()

    return results


# ── Excel 輸出 ────────────────────────────────────────────────────────────────

HEADER = ["雪場名稱", "來源網址", "關鍵字", "公告內容", "偵測到的價格", "抓取時間"]

HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(bold=True, color="FFFFFF")


def save_to_excel(items: list[FoundItem], output_dir: Path) -> Path:
    """將結果寫入 Excel，回傳檔案路徑。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = output_dir / f"ski_early_bird_{timestamp}.xlsx"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Early Bird 優惠"

    # 寫入標題列並套用樣式
    for col, header in enumerate(HEADER, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")

    # 寫入資料列
    for row_idx, item in enumerate(items, 2):
        ws.cell(row=row_idx, column=1, value=item.resort)
        ws.cell(row=row_idx, column=2, value=item.source_url)
        ws.cell(row=row_idx, column=3, value=item.keyword)
        ws.cell(row=row_idx, column=4, value=item.text)
        ws.cell(row=row_idx, column=5, value=" / ".join(item.prices) if item.prices else "未偵測到")
        ws.cell(row=row_idx, column=6, value=item.scraped_at)

    # 自動調整欄寬（上限 80）
    for col in ws.columns:
        max_len = max((len(str(c.value)) for c in col if c.value), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 80)

    wb.save(filepath)
    return filepath


# ── 資料庫預留介面 ────────────────────────────────────────────────────────────
# 未來連接 DB 時，於此實作實際的 INSERT 邏輯。
# 建議資料表欄位對應 FoundItem 的各欄位。
#
# 範例（SQLAlchemy / SQLite）：
#   engine = create_engine("sqlite:///ski_data.db")
#   with engine.begin() as conn:
#       conn.execute(text("""
#           INSERT INTO early_bird_announcements
#               (resort, source_url, keyword, text, prices, scraped_at)
#           VALUES (:resort, :source_url, :keyword, :text, :prices, :scraped_at)
#       """), [asdict(item) for item in items])

def save_to_database(items: list[FoundItem]) -> None:
    """
    預留的資料庫寫入函式。
    替換下方 TODO 區塊即可接上實際 DB。
    """
    if not items:
        return

    # TODO: 建立 DB 連線
    # TODO: 執行 INSERT（建議使用 parameterized query 防 SQL injection）
    # TODO: 關閉連線

    print(f"[DB] 預留介面：共 {len(items)} 筆待寫入資料庫（尚未實作）。")


# ── 主流程 ────────────────────────────────────────────────────────────────────

async def main() -> None:
    all_items: list[FoundItem] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            # 兩個雪場並行爬取
            tasks = [scrape_resort(browser, t) for t in TARGETS]
            for result in await asyncio.gather(*tasks):
                all_items.extend(result)
        finally:
            await browser.close()

    if all_items:
        excel_path = save_to_excel(all_items, OUTPUT_DIR)
        print(f"\n✓ Excel 已輸出：{excel_path}")
        print(f"  共 {len(all_items)} 筆結果。")
    else:
        print("\n未找到含有 Early Bird / 早鳥 關鍵字的公告。")

    # 預留：呼叫資料庫寫入
    save_to_database(all_items)


if __name__ == "__main__":
    asyncio.run(main())
