from evadm.robot import DMRobot
from evanlu.robot import NLURobot


class EvaRobot(object):
    def __init__(self, robot_id, domain_id, domain_name):
        self._dm_robot = DMRobot.get_robot(robot_id, domain_id, domain_name)
        self._nlu_robot = NLURobot.get_robot(domain_id)

    def process_question(self, question):
        question = question.strip(' \n')
        context = self._dm_robot.get_context()
        ret = self._nlu_robot.predict(context, question)
        # ret = self._dm_robot.process_request(ret["intent"],
        #                                      ret["entities"],
        #                                      ret["target_entities"],
        #                                      0)
        # self._dm_robot.process_confirm(ret["sid"], {"code": 0})
        return ret

    def train(self):
        self._nlu_robot.train()
