#!/usr/bin/env python
# encoding: utf-8


import json
import unittest
import tornado
import logging
from tornado.testing import AsyncHTTPTestCase

from evashare.log import init_logger
from evadm import ConfigLog
init_logger(level=ConfigLog.log_level, path=ConfigLog.log_path)
log = logging.getLogger(__name__)
from evadm import init_controllers
from evadm import Route
from evashare.util import uniout

init_controllers()
urls = Route.routes()
tornado_app = tornado.web.Application(urls)


class TestDM(AsyncHTTPTestCase):
    """ 测试推荐系统"""

    def get_app(self):
        return tornado_app

    def test_question(self):
        log.debug("xxxxx")
        params = {
            'robot_id': '123',
            'project': 'C',
            'sid': "sid001",
            'question': u'有什么旅游服务'
        }

        res = self.fetch("/v2/evadm/question/",
                         body=json.dumps(params),
                         method="POST")
        if not str(res.code).startswith("20"):
            errmsg = "服务器异常：http code-%s" % res.code
            raise Exception(uniout.unescape(errmsg, None))
        data = json.loads(res.body)
        assert(data["event_id"] == "travel.query:None")
        assert(data["nlu"]["intent"] == "travel.query")
        assert(data["sid"] == params["sid"])
        #  TODO:  use pytest, it always sucess now.

    def test_confirm(self):
        params = {
            'robot_id': '123',
            'project': 'C',
            'sid': "sid001",
            'result': {
                'code': 0
            }
        }
        res = self.fetch("/v2/evadm/confirm/",
                         body=json.dumps(params),
                         method="POST")
        if not str(res.code).startswith("20"):
            errmsg = "服务器异常：http code-%s" % res.code
            raise Exception(uniout.unescape(errmsg, None))
        data = json.loads(res.body)
        assert(data["code"] == 0)


if __name__ == '__main__':
    unittest.main()
