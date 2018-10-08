#!/usr/bin/env python
# encoding: utf-8
import os
from vikicommon.log import init_logger
from vikidm.config import ConfigLog

from evecms.app import setup_app
from evecms.models import Domain
from vikidm.util import PROJECT_DIR, nlu_gate
from vikidm.robot import DMRobot

data_path = os.path.join(PROJECT_DIR, "tests", "data")


app = setup_app()
app.app_context()
init_logger(level="DEBUG", path=ConfigLog.log_path)


class TestDM(object):
    """  测试对话管理引擎
    root
├── home_service
│   ├── consume.query
│   ├── home.query
│   └── left.query
├── name.query
└── travel_service
    ├── consume.query1
    ├── left.query1
    ├── spots_service
    │   ├── spots.query
    │   │   ├── @city
    │   │   ├── city
    │   │   ├── 武汉
    │   │   └── 深圳
    │   └── weather.query
    │       ├── @city,@date
    │       ├── city
    │       ├── city,date
    │       └── date
    └── travel.query
    """
    def _create_robot(self):
        # train models
        domain = Domain.query.filter_by(name="A").first()
        nlu_gate.train(str(domain.id), "A")

        self._debug_timeunit = 0.5
        self._input_data = {
            'robot_id': 'test_robot',
            'project': 'test',
            'sid': "sid001"
        }
        dm_robot = DMRobot.get_robot("test_robot", str(domain.id), domain.name)
        return dm_robot

    def test_robot(self):
        dm_robot = self._create_robot()
        dm = dm_robot._dm
        dm.debug_timeunit = 0.2
        ret = dm_robot.process_question(u"不存在的问题", "sid001")
        assert(ret["nlu"]["intent"] == "casual_talk")
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                casual_talk(STATUS_WAIT_ACTION_CONFIRM)''')
        dm_robot.process_confirm(ret['sid'], {
            'code': 0,
        })
        ret = dm_robot.process_question(u"有什么旅游服务", "sid002")
        assert(ret["code"] == 0)
        # 数据读取有问题！
        assert(ret["nlu"]["intent"] == "travel.query")
        dm_robot.process_confirm(ret['sid'], {
            'code': 0,
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                travel_service(STATUS_DELAY_EXIST)''')
        ret = dm_robot.process_question(u"消费多少", "sid003")
        #assert(ret["nlu"]["intent"] == "consume.query1")
        dm_robot.process_confirm(ret['sid'], {
            'code': 0,
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                travel_service(STATUS_DELAY_EXIST)''')
        ret = dm_robot.process_question(u"深圳什么天气", "sid004")
        assert(ret["nlu"]["intent"] == "weather.query")
        assert(ret["nlu"]["slots"] == {u"city": u"深圳"})
        dm_robot.process_confirm(ret['sid'], {
            'code': 0,
        })
        ret = dm_robot.process_question(u"深圳明天什么天气", "sid005")
        assert(ret["nlu"]["intent"] == "weather.query")
        assert(ret["nlu"]["slots"] == {u"city": u"深圳", u"date": u"明天"})
        dm_robot.process_confirm(ret['sid'], {
            'code': 0,
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                travel_service(STATUS_STACKWAIT)
                spots_service(STATUS_STACKWAIT)
                weather.query(STATUS_DELAY_EXIST)''')
        ret = dm_robot.process_question(u"附近有什么景点", "sid006")
        assert(ret["nlu"]["intent"] == "spots.query")
        assert(ret["nlu"]["slots"] == {})
        dm_robot.process_confirm(ret['sid'], {
            'code': 0,
        })

#clear_intent_question("C")
