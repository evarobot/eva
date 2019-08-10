from evanlp.ner import KeyWordEntity

indicators = {
    "dollar": ["dollar", "美元", "美金"],
    "gold": ["gold", "黄金", "元宝"]
}


def detect(text: str):
    all_values = []
    for values in indicators.values():
        all_values += values
    rst = KeyWordEntity.recognize(text, all_values)
    lan_map = {
        "美元": "dollar",
        "黄金": "gold",
        "dollar": "dollar",
        "gold": "gold"
    }
    if rst:
        return lan_map[rst[0]]
    return None