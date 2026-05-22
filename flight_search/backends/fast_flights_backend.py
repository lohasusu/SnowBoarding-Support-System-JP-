"""
Google Flights backend via fast-flights (Protobuf scraping)
不需要 API Key，直接解析 Google Flights 的 Protobuf 資料流
注意：Google 可能對頻繁請求做 IP 限速，建議每日查詢不超過 50 次
"""

import json
import os
import re
import time
from datetime import date, datetime, timedelta

from .base import BackendBase, FlightResult

try:
    from fast_flights import FlightData, Passengers
    from fast_flights import get_flights as _get_flights
    _OK = True
except ImportError:
    _OK = False

_REQUEST_DELAY = 1.5        # 每次請求最短間隔（秒）
_DAILY_WARN_THRESHOLD = 50  # 超過此次數印警告

_COUNTER_FILE = os.path.join(
    os.path.dirname(__file__), "..", "output", "daily_usage.json"
)


# ── 每日用量追蹤 ───────────────────────────────────────────────────────────────

def _load_counter() -> dict:
    try:
        with open(_COUNTER_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("date") == str(date.today()):
            return data
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    return {"date": str(date.today()), "count": 0}


def _save_counter(data: dict) -> None:
    os.makedirs(os.path.dirname(_COUNTER_FILE), exist_ok=True)
    with open(_COUNTER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


# ── 輔助函式 ──────────────────────────────────────────────────────────────────

def _parse_price(price_str: str) -> tuple[float, str]:
    """'NT$12,345' → (12345.0, 'TWD')"""
    if "NT$" in price_str or "TWD" in price_str:
        currency = "TWD"
    elif "JPY" in price_str or (price_str.startswith("¥") and "NT" not in price_str):
        currency = "JPY"
    elif "$" in price_str:
        currency = "USD"
    else:
        currency = "TWD"  # fallback：台灣 IP 預設
    nums = re.sub(r"[^\d.]", "", price_str)
    try:
        return float(nums), currency
    except ValueError:
        return 0.0, currency


def _add_days(date_str: str, days_str: str) -> str:
    """'2026-12-20' + '+1' → '2026-12-21'"""
    try:
        days = int(days_str.replace("+", ""))
        base = datetime.strptime(date_str, "%Y-%m-%d").date()
        return str(base + timedelta(days=days))
    except (ValueError, AttributeError):
        return date_str


def _parse_gf_time(time_str: str, base_date: str) -> str:
    """'6:15 AM on Sun, Dec 20' → '2026-12-20 06:15'（年份從 base_date 取）"""
    if not time_str:
        return ""
    year = base_date[:4]
    for fmt in ("%I:%M %p on %a, %b %d", "%I:%M%p on %a, %b %d"):
        try:
            dt = datetime.strptime(f"{time_str} {year}", f"{fmt} %Y")
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            pass
    # 無法解析就原樣回傳
    return time_str


def _parse_stops(stops_raw) -> int:
    """stops 有時是 int，有時是字串 'Unknown'"""
    if isinstance(stops_raw, int):
        return stops_raw
    return -1  # -1 代表未知


# ── Backend ────────────────────────────────────────────────────────────────────

class FastFlightsBackend(BackendBase):
    def __init__(self):
        self._last_req = 0.0
        self._counter = _load_counter()

    def is_available(self) -> bool:
        return _OK

    @property
    def daily_count(self) -> int:
        return self._counter["count"]

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_req
        if elapsed < _REQUEST_DELAY:
            time.sleep(_REQUEST_DELAY - elapsed)
        self._last_req = time.time()
        self._counter["count"] += 1
        _save_counter(self._counter)
        count = self._counter["count"]
        if count >= _DAILY_WARN_THRESHOLD:
            print(
                f"  ⚠️  今日已查詢 {count} 次"
                f"（建議上限 {_DAILY_WARN_THRESHOLD} 次，避免 Google IP 限速）"
            )

    def search(
        self,
        origin: str,
        destination: str,
        dest_name: str,
        departure_date: str,
        return_date: str | None,
        currency: str,
        adults: int,
    ) -> list[FlightResult]:
        self._throttle()

        trip = "round-trip" if return_date else "one-way"
        flight_data = [FlightData(date=departure_date, from_airport=origin, to_airport=destination)]
        if return_date:
            flight_data.append(FlightData(date=return_date, from_airport=destination, to_airport=origin))

        for mode in ("local", "fallback", "common"):
            try:
                result = _get_flights(
                    flight_data=flight_data,
                    trip=trip,
                    passengers=Passengers(adults=adults),
                    seat="economy",
                    fetch_mode=mode,
                )
                break
            except Exception as e:
                if mode == "common":
                    print(f"  [fast-flights 錯誤] {origin}→{destination}: {e}")
                    return []
        else:
            return []

        seen: set[tuple] = set()
        results = []
        for flight in result.flights:
            r = self._parse_flight(flight, origin, destination, dest_name, departure_date, return_date)
            if not r:
                continue
            key = (r.price, r.dep_time, r.flights_str)
            if key in seen:
                continue
            seen.add(key)
            results.append(r)
        return results

    def _parse_flight(
        self,
        flight,
        origin: str,
        destination: str,
        dest_name: str,
        departure_date: str,
        return_date: str | None,
    ) -> FlightResult | None:
        price, price_currency = _parse_price(flight.price)
        if price <= 0:
            return None

        dep_time = _parse_gf_time(flight.departure, departure_date) or departure_date
        arr_date = _add_days(departure_date, flight.arrival_time_ahead) if flight.arrival_time_ahead else departure_date
        arr_time = _parse_gf_time(flight.arrival, arr_date) if flight.arrival else ""
        stops = _parse_stops(flight.stops)

        note = f"Google Flights 即時資料 (原始: {flight.price})"
        if return_date:
            note += "；價格為去回程合計"

        return FlightResult(
            source="GoogleFlights",
            origin=origin,
            destination=destination,
            destination_name=dest_name,
            price=price,
            currency=price_currency,
            dep_time=dep_time,
            arr_time=arr_time,
            duration=flight.duration or "",
            flights_str=flight.name or f"{origin}→{destination}",
            stops=stops if stops >= 0 else 0,
            note=note,
        )
