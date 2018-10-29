#!/usr/bin/env python
# encoding: utf-8
import logging
import json
from flask import Flask
from flask import jsonify
from flask import request

from vikicommon.log import init_logger
from vikicommon.gate import cms_gate
from vikidm.config import ConfigLog, Config
from vikidm.robot import DMRobot


app = Flask(__name__)

init_logger(level="DEBUG", path=ConfigLog.log_path)
log = logging.getLogger(__name__)


@app.route('/health', methods=["GET"])
def health_cheack():
    "health cheack for sidecar"
    return jsonify({"status": "UP"})


@app.route('/v3/dm/robot/question/', methods=["GET", "POST"])
def process_question():
    """
    Process question text from human being.

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
    params = {
        "project": request.headers.get("product"),
        "robot_id": request.headers.get("sn"),
        "sid": request.headers.get("uniqueId"),
        "question": json.loads(request.data)["question"]
    }
    log.info("[REQUEST: {0}]".format(params))
    domain_id = cms_gate.get_domain_by_name(
        params["project"])["data"]["id"]
    robot = DMRobot.get_robot(params["robot_id"], domain_id,
                              params["project"])
    ret = robot.process_question(params['question'], params['sid'], params.get('conn_id'))
    return jsonify(ret)


@app.route('/dm/robot/confirm/', methods=["GET", "POST"])
def process_confirm():
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
    params = json.loads(request.data)
    log.info("[REQUEST: {0}]".format(params))
    domain_id = cms_gate.get_domain_by_name(params["project"])["data"]["id"]
    robot = DMRobot.get_robot(params["robot_id"], domain_id,
                              params["project"])
    ret = robot.process_confirm(params['sid'], params['result'])
    return jsonify(ret)


@app.route('/dm/robot/reset/', methods=["GET", "POST"])
def reset():
    params = json.loads(request.data)
    log.info("[REQUEST: {0}]".format(params))
    domain_id = cms_gate.get_domain_by_name(params["project"])["data"]["id"]
    DMRobot.reset_robot(params["robot_id"], domain_id, params["project"])
    return jsonify({"code": 0})


if __name__ == '__main__':
    app.run(host=Config.host, port=Config.port, debug=eval(Config.debug))
