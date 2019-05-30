#!/usr/bin/env python
# encoding: utf-8
import json
import logging
from flask import Flask
from flask import jsonify
from flask import request

from evashare.log import init_logger
from vikinlu.config import Config
from vikinlu.robot import NLURobot


app = Flask(__name__)

init_logger(level=Config.log_level, path=Config.log_path)
log = logging.getLogger(__name__)


@app.route("/v2/nlu/<domain_id>/predict", methods=["GET", "POST"])
def predict(domain_id):
    robot = NLURobot.get_robot(domain_id)
    data = json.loads(request.data)
    ret = robot.predict(data["context"], data["question"])
    return jsonify(ret)

@app.route('/health', methods=["GET"])
def health_cheack():
    "health cheack for sidecar"
    return jsonify({"status": "UP"})


if __name__ == '__main__':
    app.run(host=Config.host, port=Config.port, debug=eval(Config.debug))
