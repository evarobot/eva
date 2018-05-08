#!/usr/bin/env python
# encoding: utf-8

import logging
import os
import json
import requests
from vikicommon.util import uniout
from vikicommon.log import init_logger
from vikidm.config import ConfigLog
init_logger(level="DEBUG", path=ConfigLog.log_path)
log = logging.getLogger(__name__)

dm_host = "eve.axm.ai"
dm_port = 9999
cms_host = "eve.axm.ai"
cms_port = 8888



def test_question(q):
    params = {
        'robot_id': '123',
        'project': 'C',
        'sid': "sid001",
        'question': q
    }
    url = 'https://{0}:{1}/v2/robot/question/'.format(dm_host, dm_port)
    headers = { 'content-type': 'application/json' }
    v =  json.dumps(params).encode('utf8')
    data = requests.post(url, data=v,
                        headers=headers, timeout=2).text
    data = json.loads(data)
    return data

def test_confirm():
    params = {
        'robot_id': '123',
        'project': 'C',
        'sid': "sid001",
        'result': {
            'code': 0
        }
    }
    url = 'https://{0}:{1}/v2/robot/confirm/'.format(dm_host, dm_port)
    headers = { 'content-type': 'application/json' }
    v =  json.dumps(params).encode('utf8')
    data = requests.post(url, data=v,
                        headers=headers, timeout=2).text
    data = json.loads(data)


def test_login():
    params = {
        'username': 'admin',
        'password': 'admin'
    }
    url = 'https://{0}:{1}/v2/login/'.format(cms_host, cms_port)
    headers = { 'content-type': 'application/json' }
    v =  json.dumps(params).encode('utf8')
    data = requests.post(url, data=v,
                        headers=headers, timeout=2).text
    data = json.loads(data)
    log.info(data)


def test_train():
    params = { }
    url = 'https://{0}:{1}/v2/train/5aeac09aa7bf9b8f579257bc'.format(cms_host, cms_port)
    headers = { 'content-type': 'application/json' }
    v =  json.dumps(params).encode('utf8')
    data = requests.post(url, data=v,
                        headers=headers, timeout=2).text
    data = json.loads(data)
    log.info(data)


def test_reset():
    params = {
        'robot_id': 'test',
        'project': 'C'
    }
    url = 'https://{0}:{1}/v2/robot/reset/'.format(dm_host, dm_port)
    headers = { 'content-type': 'application/json' }
    v =  json.dumps(params).encode('utf8')
    data = requests.post(url, data=v,
                        headers=headers, timeout=2).text
    data = json.loads(data)

if __name__ == '__main__':
    import pprint
    while True:
        inp = raw_input("Q：")
        try:
            if inp.strip() in ["exit", "quit"]:
                break
            if inp.strip() == "reset":
                # 测试EVE
                test_reset()
                continue
            if inp.strip() == "cms":
                # 测试EVE CMS登录
                test_login()
                continue
            if inp.strip() == "train":
                # 测试EVE CMS登录
                test_train()
                continue
            if not inp:
                continue
            ret = test_question(inp)
            log.info(pprint.pformat(ret))
        except Exception as e:
            log.exception(e)
