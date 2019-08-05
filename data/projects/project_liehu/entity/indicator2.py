from evanlp.ner import KeyWordEntity

indicators = {
    "美元": ["美元", "美金"],
    "黄金": ["黄金", "元宝"]
}


def detect(text: str):
    all_values = []
    for values in indicators.values():
        all_values += values
    rst = KeyWordEntity.recognize(text, all_values)
    if len(rst) == 2:
        return rst[1]
    return None
