#!/usr/bin/env python
# encoding: utf-8
import os
import logging
import pprint
import time

from vikicommon.log import init_logger

from vikidm.util import PROJECT_DIR, cms_rpc
from vikidm.robot import DMRobot
from vikinlu.robot import NLURobot
from vikidm.context import Concept
from vikidm.config import ConfigLog, ConfigDM
from evecms.models import Domain
from vikinlu.model import IntentQuestion

data_path = os.path.join(PROJECT_DIR, "tests", "data")

init_logger(level="DEBUG", path=ConfigLog.log_path)
log = logging.getLogger(__name__)

#  TODO: train with code to prepare data #


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
        nlu_robot = NLURobot.get_robot(domain_id)
        return dm_robot, nlu_robot

    def test_mix(self):
        dm_robot, nlu_robot = self._create_robot()
        dm = dm_robot._dialog
        dm.debug_timeunit = 0.2
        ret = dm_robot.process_question("sid0001", u"消费查询")
        time.sleep((ConfigDM.input_timeout + 2) * dm.debug_timeunit)
        assert(ret["nlu"]["intent"] is None)
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)''')
        ret = dm_robot.process_question("sid0002", u"有什么旅游服务")
        assert(ret["nlu"]["intent"] == "travel.query")
        assert(ret["event_id"] == "travel.query:None")
        dm.process_confirm('sid001', {
            'code': 0,
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                Mix(travel.query)(STATUS_DELAY_EXIST)''')
        ret = dm_robot.process_question("sid0002", u"消费多少")
        assert(ret["nlu"]["intent"] == "consume.query")
        assert(ret["event_id"] == "travel.consume.query:None")
        dm.process_confirm('sid002', {
            'code': 0,
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                Mix(travel.query)(STATUS_DELAY_EXIST)''')
        ret = dm_robot.process_question("sid0003", u"深圳什么天气")
        assert(ret["nlu"]["intent"] == "weather.query")
        assert(ret["nlu"]["slots"] == { "city": u"深圳" })
        assert(ret["event_id"] == "weather.query:date")
        dm.process_confirm('sid003', {
            'code': 0,
        })
        ret = dm_robot.process_question("sid0004", u"深圳明天什么天气")
        assert(ret["nlu"]["intent"] == "weather.query")
        assert(ret["nlu"]["slots"] == { "city": u"深圳", "date": u"明天"})
        assert(ret["event_id"] == "weater.query:date,city")
        dm.process_confirm('sid004', {
            'code': 0,
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                Mix(travel.query)(STATUS_STACKWAIT)
                天气查询(STATUS_STACKWAIT)
                weather.query(STATUS_DELAY_EXIST)''')
        ret = dm_robot.process_question("sid0005", u"附近有什么景点")
        assert(ret["nlu"]["intent"] == "spots.query")
        assert(ret["event_id"] == u"spots.query:深圳")
        assert(ret["nlu"]["slots"] == {})
        dm.process_confirm('sid005', {
            'code': 0,
        })
