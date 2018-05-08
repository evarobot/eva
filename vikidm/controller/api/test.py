# encoding=utf-8
"""
推荐系统API
"""
import logging
from vikidm.libs.handler import RobotAPIHandler
from vikidm.libs.route import Route
log = logging.getLogger(__name__)

@Route('/dm/test/')
class DMResetRobotHandler(RobotAPIHandler):

    def get(self):
        log.debug("hello..")
        return self.write_json({"code": 0})
