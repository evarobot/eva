import json
from urllib.request import urlopen

import requests


def push_to_server(type, data):
    """ 推送爬虫数据到服务器中

    Parameters
    ----------
    type : str
        取值为bbc, cnn, news(tradingeconomic的数据)
    data : dict
        数据，无需修改现有爬虫返回结果的字段，直接赋值给news即可。

    Returns
    -------

    """
    params = {
        'type': type,
        'news': data
    }

    url = 'http://47.112.122.242:80/api/spiderinput'
    headers = {
        'content-type': 'application/json',
    }
    v = json.dumps(params).encode('utf8')
    ret = requests.post(url, data=v,
                        headers=headers, timeout=5)
    print(ret.status_code)
    assert (ret.status_code == 200)


def craw_trading_economics():
    url_loop = "https://tradingeconomics.com/ws/stream.ashx?start=0&size=2"
    html = urlopen(url_loop)
    s = html.read().decode("utf-8")
    json_content_list = json.loads(s)
    for doc in json_content_list:
        push_to_server("news", doc)

    data = {
         'expiration': '2019-06-17T23:59:00',
         'content': 'The New York Empire State Manufacturing Index plummeted 26.4 points from the previous month to -8.6 in June 2019, missing market expectations of +10. That was the largest monthly decline on record, due to drop in both new orders (-21.7 points to -12.0) and employment (-8.2 points to -3.5), while shipments increased at a slower pace (-6.6 points to +9.7). In addition, unfilled orders fell, and delivery times and inventories moved slightly lower. On the price front, input cost inflation was little changed, while selling price inflation slowed. Looking ahead, indexes assessing the six-month outlook indicated that firms were less optimistic about future conditions than they were last month.',
         'author': 'Joana Ferreira', 'ID': 82033, 'importance': 2,
         'category': 'NY Empire State Manufacturing Index',
         'title': 'NY Manufacturing Falls The Most on Record Iran tanker',
         'url': '/united-states/ny-empircawfawawe-state-manufacturing-index',
         'country': 'United States', 'image': '',
         'report_time': '2019-06-17', 'html': ''
    }

    push_to_server("bbc", data)
    data = {
        'expiration': '2019-06-17T23:59:00',
        'content': 'The New York Empire State Manufacturing Index plummeted 26.4 points from the previous month to -8.6 in June 2019, missing market expectations of +10. That was the largest monthly decline on record, due to drop in both new orders (-21.7 points to -12.0) and employment (-8.2 points to -3.5), while shipments increased at a slower pace (-6.6 points to +9.7). In addition, unfilled orders fell, and delivery times and inventories moved slightly lower. On the price front, input cost inflation was little changed, while selling price inflation slowed. Looking ahead, indexes assessing the six-month outlook indicated that firms were less optimistic about future conditions than they were last month.',
        'author': 'Joana Ferreira', 'ID': 82033, 'importance': 2,
        'category': 'NY Empire State Manufacturing Index',
        'title': 'NY Manufacturing Falls The Most on Record Iran tanker',
        'url': '/united-states/ny-empircawfawawe-state-manufacturing-index',
        'country': 'United States', 'image': '',
        'report_time': '2019-06-17', 'html': ''
    }

    push_to_server("bbc", data)
    data = {
        'expiration': '2019-06-17T23:59:00',
        'content': 'The New York Empire State Manufacturing Index plummeted 26.4 points from the previous month to -8.6 in June 2019, missing market expectations of +10. That was the largest monthly decline on record, due to drop in both new orders (-21.7 points to -12.0) and employment (-8.2 points to -3.5), while shipments increased at a slower pace (-6.6 points to +9.7). In addition, unfilled orders fell, and delivery times and inventories moved slightly lower. On the price front, input cost inflation was little changed, while selling price inflation slowed. Looking ahead, indexes assessing the six-month outlook indicated that firms were less optimistic about future conditions than they were last month.',
        'author': 'Joana Ferreira', 'ID': 82033, 'importance': 2,
        'category': 'Interest Rate',
        'title': 'NY Manufacturing Falls The Most on Record Iran tanker',
        'url': '/united-states/ny-empire-state-manufacturing-index',
        'country': 'United States', 'image': '',
        'report_time': 'Updated 0 927 GMT(1727 HKT) July 28, 2019', 'html': ''
    }
    push_to_server("cnn", data)
    data = {"expiration": "2018-11-22T23:59:00",
              "description": "The seasonally adjusted unemployment rate in Iceland increased to 3.1 percent in October of 2018 from an upwardly revised 1.8 percent in September. It was the highest jobless rate since July, as the number of unemployed went up by 2,800 to 6,400 and employment decreased by 1,000 to 200,400. The number of people in the labour force rose by 1,800 to 206,800 and the activity rate went up to 81.9 percent from 81.6 percent in the previous month. Meantime, the employment rate fell to 79.4 percent from 80.2 percent. A year ago, the unemployment rate was higher at 3.7 percent. ",
              "author": "Agna Gabriel", "ID": 67254,
              "importance": 1, "category": "Interest Rate",
              "title": "Iceland Jobless Rate Rises to 3.1% in October",
              "url": "/iceland/-ratdfsdfsf",
              "country": "United States", "image": None,
              "date": "2018-11-22T09:09:00", "html": None}
    push_to_server("cnn", data)





craw_trading_economics()
