"""
snowboarding_support/scraper.py — 雪票模組公開介面

使用範例：
    from snowboarding_support.scraper import get_ticket_prices, TicketItem
    prices = get_ticket_prices(region="北海道")
    prices = get_ticket_prices(name="furano")
    prices = get_ticket_prices()  # 全部雪場
"""
try:
    from .ski_early_bird_scraper import get_ticket_prices, get_ticket_prices_async, TicketItem
except ImportError:
    # 部署環境：scraper.py 被當成獨立模組載入時，相對匯入無效
    from ski_early_bird_scraper import get_ticket_prices, get_ticket_prices_async, TicketItem  # type: ignore

__all__ = ["get_ticket_prices", "get_ticket_prices_async", "TicketItem"]
