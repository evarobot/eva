#!/usr/bin/env python
# encoding: utf-8
import os
import logging
import time

from vikicommon.log import init_logger
from vikidm.config import ConfigLog, ConfigDM
init_logger(level="DEBUG", path=ConfigLog.log_path)
log = logging.getLogger(__name__)

from evecms.models import Domain
from vikidm.util import PROJECT_DIR
from vikidm.robot import DMRobot
from vikinlu.robot import NLURobot
from vikinlu.db import clear_intent_question

data_path = os.path.join(PROJECT_DIR, "tests", "data")

# train models
domain = Domain.objects.get(name="C")
robot = NLURobot.get_robot(str(domain.pk))
robot.train(("logistic", "0.1"))
robot.use_fuzzy = False


class TestDM(object):
    """  测试对话管理引擎 """
    def _create_robot(self):
        self._debug_timeunit = 0.5
        self._input_data = {
            'robot_id': 'test_robot',
            'project': 'test',
            'sid': "sid001"
        }
        domain_id = str(Domain.objects.get(name="C").pk)
        dm_robot = DMRobot.get_robot("test_robot", domain_id)
        return dm_robot

    def test_mix(self):
        dm_robot = self._create_robot()
        dm = dm_robot._dialog
        dm.debug_timeunit = 0.2
        ret = dm_robot.process_question(u"不存在的问题")
        time.sleep((ConfigDM.input_timeout + 2) * dm.debug_timeunit)
        assert(ret["nlu"]["intent"] is None)
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)''')
        ret = dm_robot.process_question(u"有什么旅游服务")
        assert(ret["nlu"]["intent"] == "travel.query")
        assert(ret["event_id"] == "travel.query:None")
        dm_robot.process_confirm(ret['sid'], {
            'code': 0,
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                Mix(travel.query)(STATUS_DELAY_EXIST)''')
        ret = dm_robot.process_question(u"消费多少")
        assert(ret["nlu"]["intent"] == "consume.query")
        assert(ret["event_id"] == "travel.consume.query:None")
        dm_robot.process_confirm(ret['sid'], {
            'code': 0,
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                Mix(travel.query)(STATUS_DELAY_EXIST)''')
        ret = dm_robot.process_question(u"深圳什么天气")
        assert(ret["nlu"]["intent"] == "weather.query")
        assert(ret["nlu"]["slots"] == {"city": u"深圳"})
        assert(ret["event_id"] == "weather.query:date")
        dm_robot.process_confirm(ret['sid'], {
            'code': 0,
        })
        ret = dm_robot.process_question(u"深圳明天什么天气")
        assert(ret["nlu"]["intent"] == "weather.query")
        assert(ret["nlu"]["slots"] == {"city": u"深圳", "date": u"明天"})
        assert(ret["event_id"] == "weater.query:date,city")
        dm_robot.process_confirm(ret['sid'], {
            'code': 0,
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                Mix(travel.query)(STATUS_STACKWAIT)
                天气查询(STATUS_STACKWAIT)
                weather.query(STATUS_DELAY_EXIST)''')
        ret = dm_robot.process_question(u"附近有什么景点")
        assert(ret["nlu"]["intent"] == "spots.query")
        assert(ret["event_id"] == u"spots.query:深圳")
        assert(ret["nlu"]["slots"] == {'city': u'深圳'})
        dm_robot.process_confirm(ret['sid'], {
            'code': 0,
        })


        clear_intent_question(str(domain.pk))
