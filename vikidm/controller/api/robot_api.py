# encoding=utf-8
"""
推荐系统API
"""
import logging
from vikidm.libs.handler import RobotAPIHandler
from vikidm.libs.route import Route
from vikidm.robot import DMRobot
from evecms.models import Domain
log = logging.getLogger(__name__)


@Route('/v2/dm/concepts/')
class QAHandler(RobotAPIHandler):

    def post(self):
        ret = {
            "name": "hello world"
        }
        domain_id = Domain.objects.get(name=self.data["project"])
        robot = DMRobot.get_robot(self.data['robot_id'], domain_id)

        return self.write_json(ret)
