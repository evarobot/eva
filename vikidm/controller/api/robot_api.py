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


@Route('/dm/robot/concepts/')
class DMHandler(RobotAPIHandler):

    def post(self):
        log.info("[REQUEST: {0}]".format(self.data))
        ret = {
            "name": "hello world"
        }
        return self.write_json(ret)


@Route('/dm/backend/concepts/')
class BackendConceptsHandler(RobotAPIHandler):

    def post(self):
        log.info("[REQUEST: {0}]".format(self.data))
        domain_id = str(Domain.objects.get(name=self.data["project"]).pk)
        robot = DMRobot.get_robot(self.data['robot_id'], domain_id)
        ret = robot.update_concepts_by_backend(self.data['concepts'])
        return self.write_json(ret)


@Route('/dm/robot/question/')
class DMQuestionHandler(RobotAPIHandler):

    def post(self):
        log.info("[REQUEST: {0}]".format(self.data))
        domain_id = str(Domain.objects.get(name=self.data["project"]).pk)
        robot = DMRobot.get_robot(self.data['robot_id'], domain_id)
        ret = robot.process_question(self.data['sid'], self.data['question'])
        return self.write_json(ret)


@Route('/dm/robot/event/')
class DMEventHandler(RobotAPIHandler):

    def post(self):
        log.info("[REQUEST: {0}]".format(self.data))
        domain_id = str(Domain.objects.get(name=self.data["project"]).pk)
        robot = DMRobot.get_robot(self.data['robot_id'], domain_id)
        ret = robot.process_question(self.data['sid'], self.data['question'])
        return self.write_json(ret)


@Route('/dm/robot/confirm/')
class DMConfirmHandler(RobotAPIHandler):

    def post(self):
        log.info("[REQUEST: {0}]".format(self.data))
        domain_id = str(Domain.objects.get(name=self.data["project"]).pk)
        robot = DMRobot.get_robot(self.data['robot_id'], domain_id)
        ret = robot.process_confirm(self.data['sid'], self.data['result'])
        return self.write_json(ret)


@Route('/dm/robot/reset/')
class DMResetRobotHandler(RobotAPIHandler):

    def post(self):
        log.info("[REQUEST: {0}]".format(self.data))
        domain_id = str(Domain.objects.get(name=self.data["project"]).pk)
        ret = DMRobot.reset_robot(self.data['robot_id'], domain_id)
        if ret:
            return self.write_json({"code": 0})
        else:
            return self.write_json({"code": -1})


@Route('/dm/robot/train/')
class DMTrainHandler(RobotAPIHandler):

    def post(self):
        log.info("[REQUEST: {0}]".format(self.data))
        from vikinlu.service import NLUService
        nlu = NLUService()
        ret = nlu.train(self.data["domain_id"], ("logistic", "0.1"))
        if ret["code"] == 0:
            return self.write_json({
                "code": 0,
                "question_num": ret["question_num"],
                "intent_questions": ret["intent_questions"],
                "message": u"训练成功!",
                "avg_precision": "adfkjdslf",
            })
        return self.write_json({
            "code": -1,
            "message": "failed"
        })
