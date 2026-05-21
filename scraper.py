"""
snowboarding_support/scraper.py — 雪票模組公開介面

使用範例：
    from snowboarding_support.scraper import get_ticket_prices, TicketItem
    prices = get_ticket_prices(region="北海道")
    prices = get_ticket_prices(name="furano")
    prices = get_ticket_prices()  # 全部雪場
"""
from .ski_early_bird_scraper import get_ticket_prices, TicketItem

__all__ = ["get_ticket_prices", "TicketItem"]
