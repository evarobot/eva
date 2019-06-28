#!/usr/bin/env python
# encoding: utf-8
import json
import logging
import time
from flask import Flask
from flask import jsonify
from flask import request
from flask_mongoengine import MongoEngine
from threading import Thread

from evashare.log import init_logger
from evashare.gate.cms import cms_gate
from vikinlu.config import ConfigMongo
from vikinlu.config import Config
from vikinlu.robot import NLURobot


app = Flask(__name__)

app.config['MONGODB_SETTINGS'] = ConfigMongo.MONGODB_SETTINGS

db = MongoEngine()

init_logger(level=Config.log_level, path=Config.log_path)
log = logging.getLogger(__name__)


def train_thread(domain_id, data):
    robot = NLURobot.get_robot(domain_id)
    now = time.time()
    ret = robot.train(("logistic", "0.1"))
    later = time.time()
    log.info("TRAIN ROBOT: {0}".format(data["project"]))
    ret["domain_name"] = data["project"]
    ret["duration"] = float(later - now)
    ret["domain_id"] = domain_id
    cms_gate.train_notify(ret)


@app.route("/v2/nlu/<domain_id>/predict", methods=["GET", "POST"])
def predict(domain_id):
    robot = NLURobot.get_robot(domain_id)
    data = json.loads(request.data)
    ret = robot.predict(data["context"], data["question"])
    return jsonify(ret)


@app.route("/v2/nlu/<domain_id>/train", methods=["GET", "POST"])
def train(domain_id):
    """
    Parameters
    ----------
    algorithm : str, Algorithm name.

    Returns
    -------
    {
        "code": 0,

        "data": {

            "intents": [

                "label": 意图标识,

                "count": 问题数量,

                "precise": 准去率,

            ]

            "total_precise": 业务准确率

        }

    }
    """
    data = json.loads(request.data)
    thread = Thread(target=train_thread, args=(domain_id, data))
    thread.start()
    return jsonify({
        "code": 0
    })


@app.route("/v2/nlu/<domain_id>/reset", methods=["GET", "POST"])
def reset(domain_id):
    data = json.loads(request.data)
    robot = NLURobot.get_robot(domain_id)
    robot.reset_robot()
    log.info("RESET ROBOT: {0}".format(data["project"]))
    return jsonify({
        "code": 0
    })


@app.route('/health', methods=["GET"])
def health_cheack():
    "health cheack for sidecar"
    return jsonify({"status": "UP"})


if __name__ == '__main__':
    db.init_app(app)
    app.run(host=Config.host, port=Config.port, debug=eval(Config.debug))
