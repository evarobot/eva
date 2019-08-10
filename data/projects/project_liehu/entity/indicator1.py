from evanlp.ner import KeyWordEntity

indicators = {
    "dollar": ["美元", "美金", "dollar"],
    "gold": ["黄金", "元宝", "gold"]
}


def detect(text: str):
    all_values = []
    for values in indicators.values():
        all_values += values
    rst = KeyWordEntity.recognize(text, all_values)
    if rst:
        return rst[0]
    return None