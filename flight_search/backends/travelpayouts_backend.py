"""
Travelpayouts (Aviasales) Data API backend

端點：GET https://api.travelpayouts.com/v1/prices/cheap
資料為快取歷史票價（非即時），適合做價格參考。

TODO: 尚未實測，取得 token 後需驗證：
  [ ] /v1/prices/cheap 回傳結構：data[destination][idx] 格式
  [ ] departure_at / return_at 時區處理
  [ ] currency 參數大小寫（TWD / twd）
  [ ] 若 destination 指定，data key 是否只有一個
  [ ] 無結果時的回傳格式
"""

import requests
from .base import BackendBase, FlightResult

_BASE_URL = "https://api.travelpayouts.com/v1/prices/cheap"


class TravelpayoutsBackend(BackendBase):
    def __init__(self, token: str):
        self.token = token

    def is_available(self) -> bool:
        return bool(self.token)

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
            "origin": origin,
            "destination": destination,
            "depart_date": departure_date,
            "currency": currency,
            "token": self.token,
        }
        if return_date:
            params["return_date"] = return_date

        try:
            resp = requests.get(_BASE_URL, params=params, timeout=15)
            resp.raise_for_status()
            body = resp.json()
        except Exception as e:
            print(f"  [Travelpayouts 錯誤] {origin}→{destination}: {e}")
            return []

        if not body.get("success"):
            return []

        results = []
        # data 結構：{ "NRT": { "0": {...}, "1": {...} }, ... }
        for dest_code, offers in body.get("data", {}).items():
            for offer in offers.values():
                r = self._parse(offer, origin, dest_code, dest_name, currency)
                if r:
                    results.append(r)
        return results

    def _parse(
        self,
        offer: dict,
        origin: str,
        destination: str,
        dest_name: str,
        currency: str,
    ) -> FlightResult | None:
        price = offer.get("price")
        if price is None:
            return None

        airline = offer.get("airline", "")
        flight_number = offer.get("flight_number", "")
        dep_time = offer.get("departure_at", "").replace("T", " ")[:16]
        ret_time = offer.get("return_at", "").replace("T", " ")[:16]
        stops = offer.get("number_of_changes", 0)

        flights_str = f"{airline}{flight_number}" if flight_number else airline

        return FlightResult(
            source="Travelpayouts",
            origin=origin,
            destination=destination,
            destination_name=dest_name,
            price=float(price),
            currency=currency,
            dep_time=dep_time,
            arr_time="",      # API 不提供
            duration="",      # API 不提供
            flights_str=flights_str,
            stops=stops,
            ret_dep_time=ret_time or None,
            note="歷史快取票價，非即時資料",
        )
