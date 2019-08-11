import json

from evanlp.ner import KeyWordEntity
from py2neo import Graph





def test_extract_event():
    with open("./bbc.json", "r") as file:
        j_data = file.read()
        d_data = json.loads(j_data)
        for doc in d_data:
            extract_event(doc["title"], doc["content"], keywords)
    with open("./cnn.json", "r") as file:
        j_data = file.read()
        d_data = json.loads(j_data)
        for doc in d_data:
            extract_event(doc["title"], doc["content"], keywords)


def test_expect_met():
    ue_above = {'expectation': 'above'}
    ue_below = {'expectation': 'below'}
    ue_same = {'expectation': 'same'}
    assert rule_news_predict('unemployment rate', ue_above) == {
        'treasury yields': 'decline',
        'usd': 'decline'
    }
    assert rule_news_predict('unemployment rate', ue_below) == {
        'treasury yields': 'rise',
        'usd': 'rise'
    }
    assert rule_news_predict('unemployment rate', ue_same) == {
        'treasury yields': 'unchange',
        'usd': 'unchange'
    }
    inf_above = {'category': 'inflation rate mom', 'expectation': 'above'}
    inf_below = {'category': 'inflation rate mom', 'expectation': 'below'}
    inf_same = {'category': 'inflation rate mom', 'expectation': 'same'}
    assert rule_news_predict('inflation rate mom', inf_above) == {
        'treasury yields': 'rise',
        'usd': 'rise'
    }
    assert rule_news_predict('inflation rate mom', inf_below) == {
        'treasury yields': 'decline',
        'usd': 'decline'
    }
    assert rule_news_predict('inflation rate mom',inf_same) == {
        'treasury yields': 'unchange',
        'usd': 'unchange'
    }


def test_event_engine():
    war = {'event': 'war'}
    assert rule_event_predict(war) == {
        'oil': 'rise',
        'gold': 'rise',
        'usd': 'decline'
     }


#test_expect_met()
#test_event_engine()