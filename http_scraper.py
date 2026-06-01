"""
http_scraper.py — 輕量 HTTP 爬蟲（不需 Playwright）
使用 httpx + BeautifulSoup4，適合 Railway 等雲端部署環境。
本地 CLI 仍使用 ski_early_bird_scraper.py（Playwright 版）。
"""
import asyncio

import httpx
from bs4 import BeautifulSoup

try:
    from .ski_early_bird_scraper import (
        TicketItem, extract_prices, is_ticket_related, load_targets,
    )
except ImportError:
    from ski_early_bird_scraper import (  # type: ignore
        TicketItem, extract_prices, is_ticket_related, load_targets,
    )

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


async def _fetch(client: httpx.AsyncClient, url: str) -> BeautifulSoup | None:
    try:
        r = await client.get(url, headers=_HEADERS, follow_redirects=True, timeout=30)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"[HTTP] 抓取失敗 {url}: {e}")
        return None


def _extract(soup: BeautifulSoup, resort: str, region: str,
             url: str, seen: set, selectors: dict) -> list[TicketItem]:
    items = []
    sel_type = selectors.get("type", "table")
    container_sel = selectors.get("container", "")
    if not container_sel:
        return items

    for container in soup.select(container_sel):
        if sel_type == "dl":
            for dt in container.find_all("dt"):
                dt_text = dt.get_text(strip=True)
                dd = dt.find_next_sibling("dd")
                dd_text = dd.get_text(strip=True) if dd else ""
                prices = extract_prices(dd_text) or extract_prices(dt_text)
                if not prices or not is_ticket_related(dt_text):
                    continue
                for price in prices:
                    key = f"{resort}||{dt_text}||{price}"
                    if key not in seen:
                        seen.add(key)
                        items.append(TicketItem(
                            resort, region, url,
                            dt_text, dt_text, price,
                        ))

        elif sel_type == "card":
            name_sel  = selectors.get("ticket_name", "")
            price_sel = selectors.get("ticket_price", "")
            if not name_sel or not price_sel:
                continue
            name_el  = container.select_one(name_sel)
            price_el = container.select_one(price_sel)
            if not name_el or not price_el:
                continue
            ticket_type = name_el.get_text(strip=True)
            prices = extract_prices(price_el.get_text(strip=True))
            if not prices or not is_ticket_related(ticket_type):
                continue
            for price in prices:
                key = f"{resort}||{ticket_type}||{price}"
                if key not in seen:
                    seen.add(key)
                    items.append(TicketItem(
                        resort, region, url,
                        ticket_type, ticket_type, price,
                    ))

        else:  # table
            row_sel = selectors.get("row", "tr")
            for row in container.select(row_sel):
                cell_texts = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
                row_text = " ".join(cell_texts)
                prices = extract_prices(row_text)
                if not prices:
                    continue
                ticket_type = next(
                    (t for t in cell_texts if t and not extract_prices(t)), ""
                )
                if not ticket_type or not is_ticket_related(ticket_type):
                    continue
                for price in prices:
                    key = f"{resort}||{ticket_type}||{price}"
                    if key not in seen:
                        seen.add(key)
                        items.append(TicketItem(
                            resort, region, url,
                            ticket_type, ticket_type, price,
                        ))

    return items


async def _scrape_one(client: httpx.AsyncClient, target: dict) -> list[TicketItem]:
    resort     = target["name"]
    region     = target.get("note", "")
    ticket_url = target.get("ticket_url")
    selectors  = target.get("selectors")

    if not ticket_url or not selectors:
        print(f"[{resort}] 略過（無 ticket_url 或 selectors）")
        return []

    selectors = {k: v for k, v in selectors.items() if not k.startswith("_")}
    soup = await _fetch(client, ticket_url)
    if not soup:
        return []

    seen: set[str] = set()
    items = _extract(soup, resort, region, ticket_url, seen, selectors)
    print(f"[{resort}] {'擷取 ' + str(len(items)) + ' 筆' if items else '未找到票價資料'}")
    return items


async def get_ticket_prices_async(
    region: str | None = None,
    name: str | None = None,
) -> list[TicketItem]:
    targets = load_targets(region=region, name=name)
    active  = [t for t in targets if t.get("ticket_url") and t.get("selectors")]

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[_scrape_one(client, t) for t in active],
            return_exceptions=True,
        )

    all_items: list[TicketItem] = []
    for r in results:
        if isinstance(r, list):
            all_items.extend(r)
    return all_items


async def stream_ticket_prices_async(
    region: str | None = None,
    name: str | None = None,
):
    """Async generator: yield (target_dict, list[TicketItem]) as each resort completes."""
    targets = load_targets(region=region, name=name)
    active  = [t for t in targets if t.get("ticket_url") and t.get("selectors")]
    if not active:
        return

    queue: asyncio.Queue = asyncio.Queue()

    async def _worker(client: httpx.AsyncClient, target: dict) -> None:
        items = await _scrape_one(client, target)
        await queue.put((target, items))

    async with httpx.AsyncClient() as client:
        tasks = [asyncio.create_task(_worker(client, t)) for t in active]
        for _ in range(len(active)):
            target, items = await queue.get()
            yield target, items
        await asyncio.gather(*tasks, return_exceptions=True)
