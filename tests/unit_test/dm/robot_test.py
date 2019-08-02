import logging
import os

from evashare.log import init_logger
from evashare.util import same_dict
from evadm import util as dm_util
from evanlu import util as nlu_util
dm_util.PROJECT_DIR = os.path.join(dm_util.PROJECT_DIR, "tests")
nlu_util.PROJECT_DIR = os.path.join(nlu_util.PROJECT_DIR, "tests")

from evadm.robot import DMRobot, EvaRobot
from evadm.config import ConfigLog

init_logger(level="DEBUG", path=ConfigLog.log_path)
log = logging.getLogger(__name__)


TEST_PROJECT = "project_cn_test"


def test_robot():
    robot0 = DMRobot.get_robot(TEST_PROJECT, TEST_PROJECT, TEST_PROJECT)
    robot = DMRobot.get_robot(TEST_PROJECT, TEST_PROJECT, TEST_PROJECT)
    assert id(robot0) == id(robot)

    robot = DMRobot.reset_robot(TEST_PROJECT, TEST_PROJECT, TEST_PROJECT)
    assert id(robot) != id(robot0)
    robot0 = DMRobot.get_robot(TEST_PROJECT, TEST_PROJECT, TEST_PROJECT)
    assert id(robot0) == id(robot)


def test_eva_robot():
    robot = EvaRobot(TEST_PROJECT, TEST_PROJECT, TEST_PROJECT)
    robot.train()
    rst = robot.process_question("帮我查一下北京今天的天气")
    target = {
        'question': '帮我查一下北京今天的天气',
        'intent': 'weather.query',
        'confidence': 1,
        'entities': {
            '@sys.date': '今天',
            '@sys.city': '北京'
        },
        'target_entities': ['meteorology', '@sys.date', '@sys.city'],
        'node_id': 'node4'
    }
    assert same_dict(rst, target)
