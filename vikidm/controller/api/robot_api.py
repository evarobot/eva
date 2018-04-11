# encoding=utf-8
"""
推荐系统API
"""
from vikidm.libs.handler import RobotAPIHandler
from vikidm.libs.route import Route


@Route('/v2/dm/concepts/')
class QAHandler(RobotAPIHandler):

    def post(self):
        return self.get()

    def get(self):
        ret = {
            "name": "hello world"
        }

        return self.write_json(ret)
