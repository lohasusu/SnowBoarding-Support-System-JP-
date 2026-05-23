"""
SerpAPI (Google Flights) backend — uses requests directly, no serpapi package needed
"""

import requests
from .base import BackendBase, FlightResult


def _mins_to_str(mins: int) -> str:
    return f"{mins // 60}h {mins % 60}m" if mins else ""


class SerpApiBackend(BackendBase):
    _BASE_URL = "https://serpapi.com/search"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def is_available(self) -> bool:
        return bool(self.api_key)

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
        params = {
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": departure_date,
            "currency": currency,
            "adults": adults,
            "type": "1" if return_date else "2",
            "api_key": self.api_key,
        }
        if return_date:
            params["return_date"] = return_date

        try:
            resp = requests.get(self._BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  [SerpAPI 錯誤] {origin}→{destination}: {e}")
            return []

        results = []
        for fg in data.get("best_flights", []) + data.get("other_flights", []):
            r = self._parse(fg, origin, destination, dest_name, currency, bool(return_date))
            if r:
                results.append(r)
        return results

    def _parse(
        self,
        fg: dict,
        origin: str,
        destination: str,
        dest_name: str,
        currency: str,
        is_round_trip: bool,
    ) -> FlightResult | None:
        price = fg.get("price")
        flights = fg.get("flights", [])
        if price is None or not flights:
            return None

        raw_dep = flights[0].get("departure_airport", {}).get("time", "")
        raw_arr = flights[-1].get("arrival_airport", {}).get("time", "")
        dep_time = raw_dep[11:16] if len(raw_dep) > 10 else raw_dep
        arr_time = raw_arr[11:16] if len(raw_arr) > 10 else raw_arr
        duration = _mins_to_str(fg.get("total_duration", 0))
        stops = len(flights) - 1

        seen: set[str] = set()
        airline_names: list[str] = []
        for f in flights:
            name = f.get("airline", "")
            if name and name not in seen:
                airline_names.append(name)
                seen.add(name)

        flights_str = " → ".join(
            "{airline} {num} ({dep}→{arr})".format(
                airline=f.get("airline", ""),
                num=f.get("flight_number", ""),
                dep=f.get("departure_airport", {}).get("id", ""),
                arr=f.get("arrival_airport", {}).get("id", ""),
            )
            for f in flights
        )

        note = "票價為去回程合計，回程班次請至 Google Flights 查看" if is_round_trip else ""

        return FlightResult(
            source="SerpAPI",
            origin=origin,
            destination=destination,
            destination_name=dest_name,
            price=float(price),
            currency=currency,
            dep_time=dep_time,
            arr_time=arr_time,
            duration=duration,
            flights_str=flights_str,
            stops=stops,
            airline_names=airline_names,
            note=note,
        )
