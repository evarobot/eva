def rule_news_predict(category, info):
    """ 使用规则分析新闻影响
    Parameters
    ----------
    category : str
       指标类型
    info : dict
       结构化数据
       {
            "expectation": "high"/"low"/"same"
       }

    Returns
    -------
    info : dict
       预测的结果
    """
    indicators = ['unemployment rate', 'retail sales mom',
                  'pce price index', 'non farm payrolls',
                  'inflation rate mom', 'gdp growth rate',
                  'balance of trade', 'wage growth']
    assert category in indicators
    predict_map = {'high': 'rise', 'low': 'decline', 'same': 'unchange'}
    if category == indicators[0]:
        predict_map = {'high': 'decline', 'low': 'rise', 'same': 'unchange'}
    real_data = info['expectation']
    predict = {'usd': predict_map[real_data],
               'treasury yields': predict_map[real_data]}
    return predict


def rule_event_predict(event):
    """ 使用规则分析事件影响
    Parameters
    ----------
    event : dict
       结构化数据
       {
            'event': war
       }

    Returns
    -------
    info : dict
       预测的结果
    """
    if not event:
        return None
    predict_map = {'war': 'rise', 'disaster': 'rise', 'politics': 'decline'}
    reverse = lambda x: 'decline' if x == 'rise' else 'rise'
    assert event['event'] in predict_map
    real_data = event['event']
    predict = {'oil': predict_map[real_data], 'gold': predict_map[real_data],
               'usd': reverse(predict_map[real_data])}
    return predict


def test_expect_met():
    ue_high = {'expectation': 'high'}
    ue_low = {'expectation': 'low'}
    ue_same = {'expectation': 'same'}
    assert rule_news_predict('unemployment rate', ue_high) == {
        'treasury yields': 'decline',
        'usd': 'decline'
    }
    assert rule_news_predict('unemployment rate', ue_low) == {
        'treasury yields': 'rise',
        'usd': 'rise'
    }
    assert rule_news_predict('unemployment rate', ue_same) == {
        'treasury yields': 'unchange',
        'usd': 'unchange'
    }
    inf_high = {'category': 'inflation rate mom', 'expectation': 'high'}
    inf_low = {'category': 'inflation rate mom', 'expectation': 'low'}
    inf_same = {'category': 'inflation rate mom', 'expectation': 'same'}
    assert rule_news_predict('inflation rate mom', inf_high) == {
        'treasury yields': 'rise',
        'usd': 'rise'
    }
    assert rule_news_predict('inflation rate mom', inf_low) == {
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


test_expect_met()
test_event_engine()