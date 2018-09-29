# encoding=utf-8
"""
推荐系统API
"""
import logging
import time
from vikidm.libs.handler import RobotAPIHandler
from vikidm.libs.route import Route
from vikidm.robot import DMRobot
from vikidm.util import cms_gate
log = logging.getLogger(__name__)


@Route('/dm/robot/slots/')
class DMHandler(RobotAPIHandler):
    """
    Methods
    -------
    post

    """

    def post(self):
        """

        URL: /dm/robot/slots/

        Parameters
        ----------
        data : {
          "robotid": ppepper的ID,

          "project": 项目名,

           "slots": {
              "XXX": "YYY"
            }
        }

        Returns
        -------
        {
            "code": 0,  // 0 -- sucess; none zero -- failed.

            "message": "",

            "event_id": "weather.query: date=今天&city=明天",

            "sid": "xxxx", // session id

            "nlu": {

                "intent": "",

                "slots": {
                    "槽1": "值1",

                    "槽2": "值2"
                }
            },
            "debug": {
                "context": "上下文变量",

                "stack": "上下文栈情况"
            },
            "action": {
                "tts": "xxxxxxxxxx",

                "web": {
                    "text": "xxxxx
                }
            }

        }

        """
        log.info("[REQUEST: {0}]".format(self.data))
        ret = {
            "name": "hello world"
        }
        return self.write_json(ret)


@Route('/dm/backend/slots/')
class BackendConceptsHandler(RobotAPIHandler):
    """
    Methods
    -------
    post

    """
    def post(self):
        """

        URL: /dm/backend/slots/

        Parameters
        ----------
        data : {
          "robotid": ppepper的ID,

          "project": 项目名,

           "slots": {
              "XXX": "YYY"
            }
        }

        Returns
        -------
        {
            "code": 0,  // 0 -- sucess; none zero -- failed.

            "message": "",

            "event_id": "weather.query: date=今天&city=明天",

            "sid": "xxxx", // session id

            "nlu": {

                "intent": "",

                "slots": {
                    "槽1": "值1",

                    "槽2": "值2"
                }
            },
            "debug": {
                "context": "上下文变量",

                "stack": "上下文栈情况"
            },
            "action": {
                "tts": "xxxxxxxxxx",

                "web": {
                    "text": "xxxxx
                }
            }

        }

        """
        log.info("[REQUEST: {0}]".format(self.data))
        domain_id = cms_gate.get_domain_by_name(
            self.data["project"])["data"]["id"]
        robot = DMRobot.get_robot(self.data["robot_id"], domain_id,
                                  self.data["project"])
        log.info("Create DM Robot: {0}".format(self.data["project"]))
        ret = robot.update_slots_by_backend(self.data['slots'])
        return self.write_json(ret)


@Route('/dm/robot/question/')
class DMQuestionHandler(RobotAPIHandler):
    """
    Process question text from human being.

    Methods
    -------
    post

    """
    def post(self):
        """

        URL: /dm/robot/question/

        Parameters
        ----------
        data : {
          "robotid": ppepper的ID,

          "project": 项目名,

          "question": "请问你叫什么名字",
        }

        Returns
        -------
        {
            "code": 0,  // 0 -- sucess; none zero -- failed.

            "message": "",

            "event_id": "weather.query: date=今天&city=明天",

            "sid": "xxxx", // session id

            "nlu": {

                "intent": "",

                "slots": {
                    "槽1": "值1",

                    "槽2": "值2"
                }
            },
            "action": {
                "tts": "xxxxxxxxxx",

                "web": {
                    "text": "xxxxx
                }
            }

        }


        """
        log.info("[REQUEST: {0}]".format(self.data))
        domain_id = cms_gate.get_domain_by_name(self.data["project"])["data"]["id"]
        robot = DMRobot.get_robot(self.data["robot_id"], domain_id,
                                  self.data["project"])
        sid = int(round(time.time() * 1000))
        ret = robot.process_question(self.data['question'], sid)
        log.info(ret)
        return self.write_json(ret)


@Route('/dm/robot/event/')
class DMEventHandler(RobotAPIHandler):
    """
    Methods
    -------
    post

    """
    def post(self):
        """

        URL: /dm/robot/event/

        Parameters
        ----------
        data : {
          "robotid": ppepper的ID,

          "project": 项目名,

          "event_id": "weather.query: date=今天&city=明天"
        }

        Returns
        -------
        {
            "code": 0,  // 0 -- sucess; none zero -- failed.

            "message": "",

            "event_id": "weather.query: date=今天&city=明天",

            "sid": "xxxx", // session id

            "nlu": {

                "intent": "",

                "slots": {
                    "槽1": "值1",

                    "槽2": "值2"
                }
            },
            "action": {
                "tts": "xxxxxxxxxx",

                "web": {
                    "text": "xxxxx
                }
            }

        }


        """

        log.info("[REQUEST: {0}]".format(self.data))
        domain_id = cms_gate.get_domain_by_name(self.data["project"])["data"]["id"]
        robot = DMRobot.get_robot(self.data["robot_id"], domain_id,
                                  self.data["project"])
        ret = robot.process_question(self.data['sid'], self.data['question'])
        return self.write_json(ret)


@Route('/dm/robot/confirm/')
class DMConfirmHandler(RobotAPIHandler):
    """
    Methods
    -------
    post

    """

    def post(self):
        """

        URL: /dm/robot/confirm/

        Parameters
        ----------
        data : {
          "robotid": ppepper的ID,

          "project": 项目名,

          "sid": "xxxx",

          "result": {
              "code": 0, // 非0表示失败

              "message": "" // 错误消息
           }
        }

        Returns
        -------
        {
            "code": 0,

            "message": ""
        }

        """
        log.info("[REQUEST: {0}]".format(self.data))
        domain_id = cms_gate.get_domain_by_name(self.data["project"])["data"]["id"]
        robot = DMRobot.get_robot(self.data["robot_id"], domain_id,
                                  self.data["project"])
        ret = robot.process_confirm(self.data['sid'], self.data['result'])
        return self.write_json(ret)


@Route('/dm/robot/reset/')
class DMResetRobotHandler(RobotAPIHandler):

    def post(self):
        log.info("[REQUEST: {0}]".format(self.data))
        domain_id = cms_gate.get_domain_by_name(self.data["project"])["data"]["id"]
        DMRobot.reset_robot(self.data["robot_id"], domain_id, self.data["project"])
        return self.write_json({"code": 0})
