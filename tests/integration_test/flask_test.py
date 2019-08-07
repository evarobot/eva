import json
import logging
import requests
from evashare.log import init_logger
from evashare.util import same_dict

from eva.config import ConfigLog

init_logger(level="DEBUG", path=ConfigLog.log_path)
log = logging.getLogger(__name__)

dm_host = "http://47.112.122.242"
dm_port = 10007

#dm_host = "http://127.0.0.1"
#dm_port = 9999


class TestDM(object):
    count = 0

    def test_question(self):
        # url = '{0}:{1}/nlu/hello'.format(dm_host, dm_port)
        # log.info(url)
        # ret = requests.get(url)
        # if ret.status_code == 200:
        #     log.info(json.loads(ret.text))
        # assert(ret.status_code == 200)
        return

    def test_train(self):
        params = {
            'project': 'project_liehu',
            'robot_id': '1234'
        }
        url = '{0}:{1}/nlu/train/'.format(dm_host, dm_port)
        headers = {
            'content-type': 'application/json',
        }
        v = json.dumps(params).encode('utf8')
        log.info(url)
        ret = requests.post(url, data=v,
                            headers=headers, timeout=5)
        assert(ret.status_code == 200)
        data = json.loads(ret.text)
        assert(data['code'] == 0)

    def test_predict(self):

        params = {
            'question': "帮我查一下美国利率新闻",
            'robot_id': '1234',
            'project': 'project_liehu'
        }
        url = '{0}:{1}/nlu/predict/'.format(dm_host, dm_port)
        headers = {
            'content-type': 'application/json',
        }
        v = json.dumps(params).encode('utf8')
        log.info(url)
        ret = requests.post(url, data=v,
                            headers=headers, timeout=5)
        assert(ret.status_code == 200)
        data = json.loads(ret.text)
        target = {
            'code': 0,
            'result': {
                'event_id': 'search',
                'sid': 0,
                'arguments': {
                    'country': '美国',
                    'category': '利率'
                }
            }
        }
        log.info(data)
        assert same_dict(data, target)

    def test_casual_talk(self):
        params = {
            'question': "我和你闲聊",
            'robot_id': '1234',
            'project': 'project_liehu'
        }
        url = '{0}:{1}/nlu/predict/'.format(dm_host, dm_port)
        headers = {
            'content-type': 'application/json',
        }
        v = json.dumps(params).encode('utf8')
        log.info(url)
        ret = requests.post(url, data=v,
                            headers=headers, timeout=5)
        assert(ret.status_code == 200)
        data = json.loads(ret.text)
        target = {
            'code': 0,
            'result': {
                'event_id': 'casual_talk',
                'sid': 0,
                'arguments': {}
            }
        }
        assert same_dict(data, target)
        log.info(data)

    def test_service(self):
        params = {
            'question': "你好。",
            'robot_id': '1234',
            'project': 'project_liehu'
        }
        url = '{0}:{1}/nlu/predict/'.format(dm_host, dm_port)
        headers = {
            'content-type': 'application/json',
        }
        v = json.dumps(params).encode('utf8')
        log.info(url)
        ret = requests.post(url, data=v,
                            headers=headers, timeout=5)
        assert(ret.status_code == 200)
        data = json.loads(ret.text)
        target = {
            'code': 0,
            'result': {
                'event_id': 'service',
                'sid': 0,
                'arguments': {},
                'speak':  "您好，有什么我可以帮你的？"
            }
        }
        assert same_dict(data, target)
        log.info(data)

    def test_event(self):
        params = {
            'question': "帮我查一下伊朗的新闻。",
            'robot_id': '1234',
            'project': 'project_liehu'
        }
        url = '{0}:{1}/nlu/predict/'.format(dm_host, dm_port)
        headers = {
            'content-type': 'application/json',
        }
        v = json.dumps(params).encode('utf8')
        log.info(url)
        ret = requests.post(url, data=v,
                            headers=headers, timeout=5)
        assert(ret.status_code == 200)
        data = json.loads(ret.text)
        target = {
            'code': 0,
            'result': {
                'event_id': 'search_event',
                'sid': 0,
                'arguments': {
                    'country': '伊朗',
                }
            }
        }
        assert same_dict(data, target)
        log.info(data)

    def test_correlation(self):
        params = {
            'question': "帮我分析一下美元和黄金的相关性",
            'robot_id': '1234',
            'project': 'project_liehu'
        }
        url = '{0}:{1}/nlu/predict/'.format(dm_host, dm_port)
        headers = {
            'content-type': 'application/json',
        }
        v = json.dumps(params).encode('utf8')
        log.info(url)
        ret = requests.post(url, data=v,
                            headers=headers, timeout=5)
        assert(ret.status_code == 200)
        data = json.loads(ret.text)
        target = {
            'code': 0,
            'result': {
                'event_id': 'correlation_analysis_without_time',
                'sid': 0,
                'arguments': {
                    'target1': '美元',
                    'target2': '黄金'
                }
            }
        }
        assert same_dict(data, target)

        params = {
            'question': "2003年",
            'robot_id': '1234',
            'project': 'project_liehu'
        }
        url = '{0}:{1}/nlu/predict/'.format(dm_host, dm_port)
        headers = {
            'content-type': 'application/json',
        }
        v = json.dumps(params).encode('utf8')
        log.info(url)
        ret = requests.post(url, data=v,
                            headers=headers, timeout=5)
        assert(ret.status_code == 200)
        data = json.loads(ret.text)
        target = {
            'code': 0,
            'result': {
                'event_id': 'correlation_analysis',
                'sid': 0,
                'arguments': {
                    'target1': '美元',
                    'target2': '黄金',
                    'datetime': '2003'
                }
            }
        }
        assert same_dict(data, target)
        log.info(data)


def iteractive():
    while True:
        inp = input("Q：")
        try:
            print(inp)
        except Exception as e:
            log.exception(e)


