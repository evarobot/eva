# encoding=utf-8
"""
推荐系统API
"""
import logging
import time
from vikinlu.robot import NLURobot
from vikidm.libs.handler import RobotAPIHandler
from vikidm.libs.route import Route
from vikidm.robot import DMRobot
from evecms.models import Domain
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
        domain_id = str(Domain.objects.get(name=self.data["project"]).pk)
        robot = DMRobot.get_robot(self.data['robot_id'], domain_id)
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
        domain_id = str(Domain.objects.get(name=self.data["project"]).pk)
        robot = DMRobot.get_robot(self.data['robot_id'], domain_id)
        ret = robot.process_question(self.data['question'])
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
        domain_id = str(Domain.objects.get(name=self.data["project"]).pk)
        robot = DMRobot.get_robot(self.data['robot_id'], domain_id)
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
        domain_id = str(Domain.objects.get(name=self.data["project"]).pk)
        robot = DMRobot.get_robot(self.data['robot_id'], domain_id)
        ret = robot.process_confirm(self.data['sid'], self.data['result'])
        return self.write_json(ret)


@Route('/dm/robot/reset/')
class DMResetRobotHandler(RobotAPIHandler):

    def post(self):
        log.info("[REQUEST: {0}]".format(self.data))
        domain_id = str(Domain.objects.get(name=self.data["project"]).pk)
        DMRobot.reset_robot(self.data['robot_id'], domain_id)
        return self.write_json({"code": 0})


@Route('/dm/robot/train/')
class DMTrainHandler(RobotAPIHandler):

    def post(self):
        log.info("[REQUEST: {0}]".format(self.data))
        robot = NLURobot.get_robot(self.data["domain_id"])
        start = time.time()
        ret = robot.train(("logistic", "0.1"))
        end = time.time()
        log.info("Training takes {0} seconds".format(end - start))
        if ret["code"] == 0:
            return self.write_json(ret.update({
                "message": u"训练成功!",
                "duration": "%.2f" % (end - start)
            }))
        return self.write_json({
            "code": -1,
            "message": "failed"
        })
