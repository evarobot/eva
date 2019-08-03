import logging
import json
from flask import request
from flask import Flask
from flask import jsonify

from evashare.log import init_logger
from eva.config import ConfigApp, ConfigLog
from eva.robot import EvaRobot


app = Flask(__name__)

init_logger(level=ConfigLog.log_level, path=ConfigLog.log_path)
log = logging.getLogger(__name__)


@app.route("/nlu/predict/", methods=["GET", "POST"])
def predict():
    data = json.loads(request.data)
    try:
        robot = EvaRobot(data["robot_id"],
                         data["project"],
                         data["project"])
        rst = robot.process_question(data["question"])
        target = {
            'code': 0,
            'result': {
                'event_id': rst["intent"],
                'arguments': rst['entities'],
                'sid': 0
            }
        }
    except:
        return jsonify({"code": -1})
    return jsonify(target)


@app.route("/nlu/train/", methods=["GET", "POST"])
def train():
    data = json.loads(request.data)
    robot = EvaRobot(data["robot_id"],
                     data["project"],
                     data["project"])
    robot.train()
    return jsonify({"code": 0})


@app.route('/health', methods=["GET"])
def health_cheack():
    return jsonify({"status": "UP"})


if __name__ == '__main__':
    app.run(host=ConfigApp.host, port=ConfigApp.port, debug=eval(ConfigApp.debug))
