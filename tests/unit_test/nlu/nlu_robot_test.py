import logging
import os

from evanlu import util

util.PROJECT_DIR = os.path.join(util.PROJECT_DIR, "tests")


from evashare.log import init_logger
from evashare.util import same_dict
from evanlu.config import ConfigLog
from evanlu.robot import NLURobot


init_logger(level="DEBUG", path=ConfigLog.log_path)
log = logging.getLogger(__name__)


TEST_PROJECT = "project_cn_test"


def test_robot():
    robot0 = NLURobot.get_robot(TEST_PROJECT)
    robot = NLURobot.get_robot(TEST_PROJECT)

    assert id(robot0) == id(robot)

    robot = NLURobot.reset_robot(TEST_PROJECT)
    assert id(robot) != id(robot0)
    robot0 = NLURobot.get_robot(TEST_PROJECT)
    assert id(robot0) == id(robot)

    robot0.train()
    context = {
        "intent": None,
        "agents": [("weather.query", "weather.query", "node4")]
    }
    rst = robot0.predict(context, "帮我查一下北京今天的天气")
    target = {
        'question': '帮我查一下北京今天的天气',
        'intent': 'weather.query',
        'confidence': 1,
        'entities': {
             'date': '今天',
             'city': '北京'
        },
         'target_entities': ['meteorology', 'date', 'city'],
         'node_id': 'node4'
    }
    assert same_dict(rst, target)
