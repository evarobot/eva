# encoding=utf-8
"""
推荐系统API
"""
import logging
from vikidm.libs.handler import RobotAPIHandler
from vikidm.libs.route import Route
from vikidm.robot import DMRobot
log = logging.getLogger(__name__)


@Route('/v2/dm/concepts/')
class QAHandler(RobotAPIHandler):

    def post(self):
        ret = {
            "name": "hello world"
        }
        robot = DMRobot.get_robot(self.data['robot_id'], self.data['project'])

        return self.write_json(ret)
