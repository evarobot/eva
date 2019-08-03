import logging
import os

from evashare.log import init_logger
from evadm import util as dm_util
dm_util.PROJECT_DIR = os.path.join(dm_util.PROJECT_DIR, "tests")

from evadm.robot import DMRobot
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

