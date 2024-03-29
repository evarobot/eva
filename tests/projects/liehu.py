import logging
from pprint import pprint

from evashare.log import init_logger
from evashare.util import same_dict

from eva.robot import EvaRobot
from evadm.config import ConfigLog

init_logger(level="DEBUG", path=ConfigLog.log_path)
log = logging.getLogger(__name__)


TEST_PROJECT = "project_liehu"


def test_eva_robot():
    robot = EvaRobot(TEST_PROJECT, TEST_PROJECT, TEST_PROJECT)
    robot.train()

    rst = robot.process_question("帮我查一下美国利率新闻")
    # todo query answer json in evarobot
    target = {
        'intent': 'search',
        'sid': 0,
        'response_id': 'search',
        'nlu': {
            'intent': 'search',
            'slots': {
                'country': 'United States',
                'category': 'Interest Rate'
            }
        }
    }
    assert same_dict(rst, target)
    rst = robot.process_question("帮我查一下伊朗的新闻")
    from pprint import pprint
    pprint(rst)

    rst = robot.process_question("分析一下美元和黄金的相关性")
    pprint(rst)
    rst = robot.process_question("2003年")
    rst = robot.process_question("二零零三年")
    pprint(rst)


def test_en_robot():
    robot = EvaRobot(TEST_PROJECT, TEST_PROJECT, TEST_PROJECT)
    robot.train()

    rst = robot.process_question("show me American interest rate")
    # todo query answer json in evarobot
    target = {
        'intent': 'search',
        'sid': 0,
        'response_id': 'search',
        'nlu': {
            'intent': 'search',
            'slots': {
                'country': 'United States',
                'category': 'Interest Rate'
            }
        }
    }
    assert same_dict(rst, target)
