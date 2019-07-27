import logging
import os

from evashare.log import init_logger

from evanlu.robot import NLURobot
from evanlu.config import ConfigLog
from evanlu.io import NLUFileIO
from evanlu.util import PROJECT_DIR

init_logger(level="DEBUG", path=ConfigLog.log_path)
log = logging.getLogger(__name__)


TEST_PROJECT = "project_cn_test"
file_io = NLUFileIO(TEST_PROJECT)
file_io._project_path = os.path.join(
    PROJECT_DIR, "tests", "data", "projects", TEST_PROJECT)
file_io._sys_path = os.path.join(
    PROJECT_DIR, "tests", "data", "projects", "sys")


def test_robot():
    robot0 = NLURobot.get_robot("project_cn_test")
    robot = NLURobot.get_robot("project_cn_test")
    assert id(robot0) == id(robot)

    robot = NLURobot.reset_robot("project_cn_test")
    assert id(robot) != id(robot0)
    robot0 = NLURobot.get_robot("project_cn_test")
    assert id(robot0) == id(robot)

    robot.train()
    context = [("name.query", "name.query", "node4")]
    robot.predict(context, "你叫什么名字")
    # TODO

