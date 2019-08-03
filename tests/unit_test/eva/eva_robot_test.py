import logging
import os

from evashare.log import init_logger
from evashare.util import same_dict
from evadm import util as dm_util
from evanlu import util as nlu_util
dm_util.PROJECT_DIR = os.path.join(dm_util.PROJECT_DIR, "tests")
nlu_util.PROJECT_DIR = os.path.join(nlu_util.PROJECT_DIR, "tests")

from eva.robot import EvaRobot
from evadm.config import ConfigLog

init_logger(level="DEBUG", path=ConfigLog.log_path)
log = logging.getLogger(__name__)


TEST_PROJECT = "project_cn_test"


def test_eva_robot():
    robot = EvaRobot(TEST_PROJECT, TEST_PROJECT, TEST_PROJECT)
    robot.train()
    rst = robot.process_question("帮我查一下北京今天的天气")
    # todo query answer json in evarobot
    target = {
        'intent': 'weather.query',
        'nlu': {
            'intent': 'weather.query',
            'slots': {
                'city': '北京',
                'date': '今天'
            }
        },
        'response_id': 'result',
        'sid': 0
    }
    assert same_dict(rst, target)
