AIRPORT_ZH = {
    "TPE": "台北桃園", "TSA": "台北松山",
    "KHH": "高雄", "RMQ": "台中",
    "CTS": "新千歲（北海道）", "NRT": "東京成田",
    "HND": "東京羽田", "KIX": "大阪關西",
    "NGO": "名古屋中部", "SDJ": "仙台",
    "AOJ": "青森", "GAJ": "山形",
    "OKA": "沖繩那霸",
}

AIRLINE_ZH = {
    "EVA Air": "長榮航空",
    "China Airlines": "中華航空",
    "Starlux Airlines": "星宇航空",
    "Tigerair Taiwan": "台灣虎航",
    "AirAsia": "亞洲航空",
    "Peach Aviation": "樂桃航空",
    "Japan Airlines": "日本航空",
    "All Nippon Airways": "全日空",
    "ANA": "全日空",
    "JAL": "日本航空",
}

def airport_label(code: str) -> str:
    """Return 'TPE 台北桃園' or just 'TPE' if not in map."""
    zh = AIRPORT_ZH.get(code.upper(), "")
    return f"{code} {zh}" if zh else code

def airline_label(name: str) -> str:
    """Return Chinese airline name if available, else original."""
    return AIRLINE_ZH.get(name, name)
