from evanlp.ner import KeyWordEntity


def detect(text: str):
    result = KeyWordEntity.recognize(text, ["2003", "二零零三", "2013", "二零一三"])
    if result:
        return result[0]
    else:
        return None