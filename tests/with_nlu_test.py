#!/usr/bin/env python
# encoding: utf-8
import os
import time
from vikicommon.log import init_logger
from vikidm.config import ConfigLog, ConfigDM

from evecms.app import setup_app
from evecms.models import Domain
from vikidm.util import PROJECT_DIR, nlu_train
from vikidm.robot import DMRobot

data_path = os.path.join(PROJECT_DIR, "tests", "data")


app = setup_app()
app.app_context()
init_logger(level="DEBUG", path=ConfigLog.log_path)


class TestDM(object):
    """  测试对话管理引擎
    ├── Mix(home.service)
    │   ├── consume.query
    │   ├── home.service
    │   └── left.query
    ├── Mix(travel.query)
    │   ├── consume.query
    │   ├── left.query
    │   ├── travel.query
    │   └── 天气查询
    │       ├── spots.query
    │       │   ├── @city
    │       │   ├── 武汉
    │       │   └── 深圳
    │       └── weather.query
    │           ├── @date,@city
    │           ├── city
    │           ├── date
    │           └── default
    ├── location.query
    │   ├── 周黑鸭
    │   └── 耐克
    └── name.query
    """
    def _create_robot(self):
        # train models
        domain = Domain.query.filter_by(name="C").first()
        nlu_train(str(domain.id))

        self._debug_timeunit = 0.5
        self._input_data = {
            'robot_id': 'test_robot',
            'project': 'test',
            'sid': "sid001"
        }
        dm_robot = DMRobot.get_robot("test_robot", str(domain.id))
        return dm_robot

    def test_robot(self):
        dm_robot = self._create_robot()
        dm = dm_robot._dm
        dm.debug_timeunit = 0.2
        ret = dm_robot.process_question(u"不存在的问题")
        time.sleep((ConfigDM.input_timeout + 2) * dm.debug_timeunit)
        assert(ret["nlu"]["intent"] == "casual_talk")
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)''')
        ret = dm_robot.process_question(u"有什么旅游服务")
        assert(ret["code"] == 0)
        # 数据读取有问题！
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
        assert(ret["nlu"]["slots"] == {u"city槽": u"深圳"})
        assert(ret["event_id"] == "weather.query:date")
        dm_robot.process_confirm(ret['sid'], {
            'code': 0,
        })
        ret = dm_robot.process_question(u"深圳明天什么天气")
        assert(ret["nlu"]["intent"] == "weather.query")
        assert(ret["nlu"]["slots"] == {u"city槽": u"深圳", u"date槽": u"明天"})
        assert(ret["event_id"] == "weather.query:date,city")
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
        assert(ret["nlu"]["slots"] == {})
        dm_robot.process_confirm(ret['sid'], {
            'code': 0,
        })

#clear_intent_question("C")
