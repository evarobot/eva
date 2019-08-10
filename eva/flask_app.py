import logging
import json
from flask import request
from flask import Flask
from flask import jsonify
from py2neo import Graph

from evashare.log import init_logger
from eva.config import ConfigApp, ConfigLog
from eva.robot import EvaRobot


app = Flask(__name__)

init_logger(level=ConfigLog.log_level, path=ConfigLog.log_path)
log = logging.getLogger(__name__)


@app.route("/nlu/predict/", methods=["GET", "POST"])
def predict():
    data = json.loads(request.data)
    robot = EvaRobot(data["robot_id"],
                     data["project"],
                     data["project"])
    rst = robot.process_question(data["question"])
    # hack code
    if rst["response_id"] == "search_event":
        rst["nlu"]["slots"]["country"] = rst["nlu"]["slots"]["event_country"]
        del rst["nlu"]["slots"]["event_country"]
    target = {
        'code': 0,
        'result': {
            'event_id': rst["response_id"],
            'arguments': rst['nlu']["slots"],
            'sid': 0
        }
    }
    if rst["response_id"] == "service":
        target["result"]["speak"] = "您好，有什么我可以帮你的？"
    if rst["response_id"] == "correlation_analysis_without_time":
        target["result"]["speak"] = "您好，请问您想分析的是哪段时间？"
    return jsonify(target)


@app.route("/nlu/graph/", methods=["GET", "POST"])
def show_graph():
    g = Graph("bolt://47.112.122.242:7687",
              user="neo4j",
              password="Password01")
    results = g.run("MATCH (n1)-[r]->(n2) RETURN r, n1, n2")
    const_links = []
    const_nodes = []
    for record in results:
        d_node1 = dict(dict(record)['n1'])
        d_node2 = dict(dict(record)['n2'])
        const_nodes.append({
            'name': d_node1["name"],
            'symbolSize': 30,
            'itemStyle': {
                "color": "red"
            }
        })
        const_links.append({
            "source": d_node1["name"],
            "target": d_node2["name"],
            "value": type(dict(record)['r']).__name__
        })
    return jsonify({
        "code": 0,
        "data": {
            "const_nodes": const_nodes,
            "const_links": const_links
        }
    })


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
